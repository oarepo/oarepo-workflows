#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Flask extension for workflows."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional

import importlib_metadata
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_records_resources.services.uow import RecordCommitOp, unit_of_work
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from oarepo_workflows.errors import InvalidWorkflowError, MissingWorkflowError
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.services.auto_approve import (
    AutoApproveEntityService,
    AutoApproveEntityServiceConfig,
)
from oarepo_workflows.services.multiple_entities import (
    MultipleEntitiesEntityService,
    MultipleEntitiesEntityServiceConfig,
)

if TYPE_CHECKING:
    from flask import Flask
    from flask_principal import Identity
    from invenio_drafts_resources.records import ParentRecord, Record
    from invenio_records_resources.services.uow import UnitOfWork

    from oarepo_workflows.base import (
        StateChangedNotifier,
        Workflow,
        WorkflowChangeNotifier,
    )
    from oarepo_workflows.records.systemfields.workflow import WithWorkflow


class OARepoWorkflows:
    """OARepo workflows extension."""

    def __init__(self, app: Optional[Flask] = None) -> None:
        """Initialize the extension.

        :param app: Flask application to initialize with.
        If not passed here, it can be passed later using init_app method.
        """
        if app:
            self.init_config(app)
            self.init_app(app)
            self.init_services()

    # noinspection PyMethodMayBeStatic
    def init_config(self, app: Flask) -> None:
        """Initialize configuration.

        :param app: Flask application to initialize with.
        """
        from . import ext_config

        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}

        for k in ext_config.OAREPO_PERMISSIONS_PRESETS:
            if k not in app.config["OAREPO_PERMISSIONS_PRESETS"]:
                app.config["OAREPO_PERMISSIONS_PRESETS"][k] = (
                    ext_config.OAREPO_PERMISSIONS_PRESETS[k]
                )

        app.config.setdefault("WORKFLOWS", ext_config.WORKFLOWS)

        app.config.setdefault(
            "OAREPO_WORKFLOWS_SET_REQUEST_PERMISSIONS",
            ext_config.OAREPO_WORKFLOWS_SET_REQUEST_PERMISSIONS,
        )

        app.config.setdefault("REQUESTS_ALLOWED_RECEIVERS", []).extend(
            ext_config.WORKFLOWS_ALLOWED_REQUEST_RECEIVERS
        )

    def init_services(self) -> None:
        """Initialize workflow services."""
        # noinspection PyAttributeOutsideInit
        self.auto_approve_service = AutoApproveEntityService(
            config=AutoApproveEntityServiceConfig()
        )
        self.multiple_recipients_service = MultipleEntitiesEntityService(
            config=MultipleEntitiesEntityServiceConfig()
        )

    @cached_property
    def state_changed_notifiers(self) -> list[StateChangedNotifier]:
        """Return a list of state changed notifiers.

        State changed notifiers are callables that are called when a state of a record changes,
        for example as a result of a workflow transition.

        They are registered as entry points in the group `oarepo_workflows.state_changed_notifiers`.
        """
        group_name = "oarepo_workflows.state_changed_notifiers"
        return [
            x.load() for x in importlib_metadata.entry_points().select(group=group_name)
        ]

    @cached_property
    def workflow_changed_notifiers(self) -> list[WorkflowChangeNotifier]:
        """Return a list of workflow changed notifiers.

        Workflow changed notifiers are callables that are called when a workflow of a record changes.
        They are registered as entry points in the group `oarepo_workflows.workflow_changed_notifiers`.
        """
        group_name = "oarepo_workflows.workflow_changed_notifiers"
        return [
            x.load() for x in importlib_metadata.entry_points().select(group=group_name)
        ]

    @unit_of_work()
    def set_state(
        self,
        identity: Identity,
        record: Record,
        new_state: str,
        *args: Any,
        uow: UnitOfWork,
        commit: bool = True,
        **kwargs: Any,
    ) -> None:
        """Set a new state on a record.

        :param identity:    identity of the user who initiated the state change
        :param record:      record whose state is being changed
        :param new_state:   new state to set
        :param args:        additional arguments
        :param uow:         unit of work
        :param commit:      whether to commit the change
        :param kwargs:      additional keyword arguments
        """
        previous_value = record.state
        record.state = new_state
        if commit:
            service = get_record_service_for_record(record)
            uow.register(RecordCommitOp(record, indexer=service.indexer))
        for state_changed_notifier in self.state_changed_notifiers:
            state_changed_notifier(
                identity, record, previous_value, new_state, *args, uow=uow, **kwargs
            )

    @unit_of_work()
    def set_workflow(
        self,
        identity: Identity,
        record: Record,
        new_workflow_id: str,
        *args: Any,
        uow: UnitOfWork,
        commit: bool = True,
        **kwargs: Any,
    ) -> None:
        """Set a new workflow on a record.

        :param identity:            identity of the user who initiated the workflow change
        :param record:              record whose workflow is being changed
        :param new_workflow_id:     new workflow to set
        :param args:                additional arguments
        :param uow:                 unit of work
        :param commit:              whether to commit the change
        :param kwargs:              additional keyword arguments
        """
        if new_workflow_id not in current_oarepo_workflows.record_workflows:
            raise InvalidWorkflowError(
                f"Workflow {new_workflow_id} does not exist in the configuration.",
                record=record,
            )
        parent = record.parent  # noqa for typing: we do not have a better type for record with parent
        previous_value = parent.workflow
        parent.workflow = new_workflow_id
        if commit:
            service = get_record_service_for_record(record)
            uow.register(
                ParentRecordCommitOp(parent, indexer_context=dict(service=service))
            )
        for workflow_changed_notifier in self.workflow_changed_notifiers:
            workflow_changed_notifier(
                identity,
                record,
                previous_value,
                new_workflow_id,
                *args,
                uow=uow,
                **kwargs,
            )

    # noinspection PyMethodMayBeStatic
    def get_workflow_from_record(self, record: Record | ParentRecord) -> str | None:
        """Get the workflow from a record.

        :param record:  record to get the workflow from. Can pass either a record or its parent.
        """
        parent: ParentRecord = record.parent if hasattr(record, "parent") else record

        if hasattr(parent, "workflow") and parent.workflow:
            return parent.workflow
        else:
            return None

    @property
    def record_workflows(self) -> dict[str, Workflow]:
        """Return a dictionary of available record workflows."""
        return self.app.config["WORKFLOWS"]

    @property
    def default_workflow_events(self) -> dict:
        """Return a dictionary of default workflow events.

        Default workflow events are those that can be added to any request.
        The dictionary is taken from the configuration key `DEFAULT_WORKFLOW_EVENTS`.
        """
        return self.app.config.get("DEFAULT_WORKFLOW_EVENTS", {})

    def get_workflow(self, record: Record | dict[str, Any]) -> Workflow:
        """Get the workflow for a record.

        :param record:  record to get the workflow for
        :raises MissingWorkflowError: if the workflow is not found
        :raises InvalidWorkflowError: if the workflow is invalid
        """
        if hasattr(record, "parent"):
            try:
                record_parent: WithWorkflow = record.parent  # noqa for typing: we do not have a better type for record with parent
            except AttributeError as e:
                raise MissingWorkflowError(
                    "Record does not have a parent attribute, is it a draft-enabled record?",
                    record=record,
                ) from e
            try:
                workflow_id = record_parent.workflow
            except AttributeError as e:
                raise MissingWorkflowError(
                    "Parent record does not have a workflow attribute.", record=record
                ) from e
        else:
            try:
                dict_parent: dict[str, Any] = record["parent"]
            except KeyError as e:
                raise MissingWorkflowError(
                    "Record does not have a parent attribute.", record=record
                ) from e
            try:
                workflow_id = dict_parent["workflow"]
            except KeyError as e:
                raise MissingWorkflowError(
                    "Parent record does not have a workflow attribute.", record=record
                ) from e

        try:
            return self.record_workflows[workflow_id]
        except KeyError as e:
            raise InvalidWorkflowError(
                f"Workflow {workflow_id} doesn't exist in the configuration.",
                record=record,
            ) from e

    def init_app(self, app: Flask) -> None:
        """Flask application initialization."""
        # noinspection PyAttributeOutsideInit
        self.app = app
        app.extensions["oarepo-workflows"] = self


def finalize_app(app: Flask) -> None:
    """Finalize the application.

    This function registers the auto-approve service in the records resources registry.
    It is called from invenio_base.api_finalize_app entry point.

    :param app: Flask application
    """
    records_resources = app.extensions["invenio-records-resources"]

    ext: OARepoWorkflows = app.extensions["oarepo-workflows"]

    records_resources.registry.register(
        ext.auto_approve_service,
        service_id=ext.auto_approve_service.config.service_id,
    )

    records_resources.registry.register(
        ext.multiple_recipients_service,
        service_id=ext.multiple_recipients_service.config.service_id,
    )

    if app.config["OAREPO_WORKFLOWS_SET_REQUEST_PERMISSIONS"]:
        patch_request_permissions(app)


def patch_request_permissions(app: Flask) -> None:
    """Replace invenio request permissions.

    If permissions for requests are the plain invenio permissions,
    replace those with workflow-based ones. If user set their own
    permissions, keep those intact.
    """
    # patch invenio requests
    from invenio_requests.services.permissions import (
        PermissionPolicy as OriginalPermissionPolicy,
    )

    with app.app_context():
        from invenio_requests.proxies import current_requests_service

        from oarepo_workflows.requests.permissions import (
            CreatorsFromWorkflowRequestsPermissionPolicy,
        )

        current_permission_policy = app.config.get("REQUESTS_PERMISSION_POLICY")
        if current_permission_policy is OriginalPermissionPolicy:
            app.config["REQUESTS_PERMISSION_POLICY"] = (
                CreatorsFromWorkflowRequestsPermissionPolicy
            )
            assert (
                current_requests_service.config.permission_policy_cls
                is CreatorsFromWorkflowRequestsPermissionPolicy
            )
