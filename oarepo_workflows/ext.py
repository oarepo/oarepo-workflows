#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Flask extension for workflows."""

from __future__ import annotations

import importlib.metadata
from functools import cached_property
from typing import TYPE_CHECKING, Any, cast

from invenio_records_resources.services.uow import unit_of_work

from oarepo_workflows.errors import (
    InvalidWorkflowError,
    MissingWorkflowError,
    UnregisteredRequestTypeError,
)
from oarepo_workflows.services.auto_approve import (
    AutoApproveService,
    AutoApproveServiceConfig,
)
from oarepo_workflows.services.multiple_entities import (
    MultipleEntitiesEntityService,
    MultipleEntitiesEntityServiceConfig,
)
from oarepo_workflows.services.uow import StateChangeOperation

if TYPE_CHECKING:
    from flask import Flask
    from flask_principal import Identity
    from invenio_drafts_resources.records import Record
    from invenio_records_resources.services.uow import UnitOfWork

    from oarepo_workflows.base import (
        StateChangedNotifier,
        Workflow,
    )
    from oarepo_workflows.records.systemfields.workflow import WithWorkflow
    from oarepo_workflows.requests.events import WorkflowEvent


class OARepoWorkflows:
    """OARepo workflows extension."""

    def __init__(self, app: Flask | None = None) -> None:
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

        app.config.setdefault("WORKFLOWS", ext_config.WORKFLOWS)
        app.config.setdefault("REQUESTS_ALLOWED_RECEIVERS", []).extend(ext_config.WORKFLOWS_ALLOWED_REQUEST_RECEIVERS)

    def init_app(self, app: Flask) -> None:
        """Flask application initialization."""
        # noinspection PyAttributeOutsideInit
        self.app = app
        app.extensions["oarepo-workflows"] = self

    def init_services(self) -> None:
        """Initialize workflow services."""
        # noinspection PyAttributeOutsideInit
        self.auto_approve_service = AutoApproveService(AutoApproveServiceConfig())
        self.multiple_recipients_service = MultipleEntitiesEntityService(MultipleEntitiesEntityServiceConfig())

    @cached_property
    def workflow_by_code(self) -> dict[str, Workflow]:
        """Return workflow by workflow code."""
        return {w.code: w for w in self.app.config["WORKFLOWS"]}

    @cached_property
    def state_changed_notifiers(self) -> list[StateChangedNotifier]:
        """Return a list of state changed notifiers.

        State changed notifiers are callables that are called when a state of a record changes,
        for example as a result of a workflow transition.

        They are registered as entry points in the group `oarepo_workflows.state_changed_notifiers`.
        """
        group_name = "oarepo_workflows.state_changed_notifiers"
        return [ep.load() for ep in importlib.metadata.entry_points(group=group_name)]

    @unit_of_work()
    def set_state(  # noqa: PLR0913
        self,
        identity: Identity,
        record: Record,
        new_state: str,
        *args: Any,
        uow: UnitOfWork,
        commit: bool = True,
        notify_later: bool = True,
        **kwargs: Any,
    ) -> None:
        """Set a new state on a record.

        :param identity:    identity of the user who initiated the state change
        :param record:      record whose state is being changed
        :param new_state:   new state to set
        :param args:        additional arguments
        :param uow:         unit of work
        :param commit:      whether to commit the change
        :param notify_later: run the notification in post commit hook, not immediately
        :param kwargs:      additional keyword arguments
        """
        uow.register(
            StateChangeOperation(
                identity,
                record,
                new_state,
                *args,
                commit_record=commit,
                notify_later=notify_later,
                extra_kwargs=kwargs,
            )
        )

    @property
    def record_workflows(self) -> list[Workflow]:
        """Return a dictionary of available record workflows."""
        return self.app.config["WORKFLOWS"]  # type: ignore[no-any-return]

    @property
    def default_workflow_events(self) -> dict[str, WorkflowEvent]:
        """Return a dictionary of default workflow events.

        Default workflow events are those that can be added to any request.
        The dictionary is taken from the configuration key `DEFAULT_WORKFLOW_EVENTS`.
        """
        return cast(
            "dict[str, WorkflowEvent]",
            self.app.config.get("DEFAULT_WORKFLOW_EVENTS", {}),
        )

    def get_workflow(self, record: Record | dict[str, Any]) -> Workflow:
        """Get the workflow for a record.

        :param record:  record to get the workflow for
        :raises MissingWorkflowError: if the workflow is not found
        :raises InvalidWorkflowError: if the workflow is invalid
        """
        if hasattr(record, "parent"):
            try:
                record_parent: WithWorkflow = record.parent  # type: ignore[reportAttributeAccessIssue]
            except AttributeError as e:  # TODO: hasattr(record, "parent") already tested?
                raise MissingWorkflowError(
                    "Record does not have a parent attribute, is it a draft-enabled record?",
                    record=record,
                ) from e
            try:
                workflow_id = record_parent.workflow
            except AttributeError as e:
                raise MissingWorkflowError("Parent record does not have a workflow attribute.", record=record) from e
        else:
            try:
                dict_parent: dict[str, Any] = record["parent"]
            except KeyError as e:
                raise MissingWorkflowError("Record does not have a parent attribute.", record=record) from e
            try:
                workflow_id = cast("str", dict_parent["workflow"])
            except KeyError as e:
                raise MissingWorkflowError("Parent record does not have a workflow attribute.", record=record) from e
        try:
            return self.workflow_by_code[workflow_id]
        except KeyError as e:
            raise InvalidWorkflowError(
                f"Workflow {workflow_id} doesn't exist in the configuration.",
                record=record,
            ) from e


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

    for workflow in ext.record_workflows:
        for r in workflow.requests().requests:
            try:
                r.request_type  # noqa B018
            # TODO: ugly; how to test?
            except KeyError as e:
                raise UnregisteredRequestTypeError(r._request_type) from e  # noqa SLF001
