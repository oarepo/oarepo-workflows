#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Permission generators usable in workflow configurations."""

from __future__ import annotations

import logging
import operator
import warnings
from functools import reduce
from typing import TYPE_CHECKING, Any, override

from flask import current_app
from flask_principal import Identity, RoleNeed
from invenio_access import ActionNeed
from invenio_records_permissions.generators import Generator
from invenio_records_permissions.generators import SameAs as InvenioSameAs
from invenio_search.engine import dsl
from oarepo_runtime.services.generators import (
    ConditionalGenerator,
)

from oarepo_workflows.errors import InvalidWorkflowError, MissingWorkflowError
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests import RecipientGeneratorMixin

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from flask_principal import Need
    from invenio_records_permissions.generators import Generator as InvenioGenerator
    from invenio_records_resources.records import Record
    from invenio_requests.customizations.request_types import RequestType

    from oarepo_workflows import Workflow
    from oarepo_workflows.services.permissions import BaseWorkflowPermissionPolicy

log = logging.getLogger(__name__)


def query_filters_from_all_workflows(action: str, **context: Any) -> list[dsl.query.Query]:
    """Get query filters to match records depending on the records' workflow."""
    workflows = current_oarepo_workflows.record_workflows
    queries = []
    for workflow in workflows:
        q_in_workflow = dsl.Q("term", **{"parent.workflow": workflow.code})
        if workflow.code == current_oarepo_workflows.default_workflow.code:
            q_in_workflow = q_in_workflow | ~dsl.Q("exists", field="parent.workflow")
        workflow_filters = workflow.permissions(action, **context).query_filters
        if not workflow_filters:
            workflow_filters = [dsl.Q("match_none")]
        query = reduce(lambda f1, f2: f1 | f2, workflow_filters) & q_in_workflow
        queries.append(query)
    return [q for q in queries if q]


class InAnyWorkflow(Generator):
    """InAnyWorkflow generator.

    Warning: if some workflow uses generators with excludes, they can clash with needs in different workflows leading
    to the generator excluding users even though they are allowed in the workflow without the excludes generator.
    This is due to how flask allows() is implemented.

    Eg. If workflow 1 defines provides need for User 1 and Workflow 2 excludes User 1,
    the generator will treat user 1 as excluded despite being allowed in the first workflow.
    """

    def __init__(self, action: str) -> None:
        """Construct the generator."""
        self._action = action

    @override
    def needs(self, **context: Any) -> Sequence[Need]:
        ret = set()
        for workflow in current_oarepo_workflows.record_workflows:
            ret |= set(workflow.permissions(self._action, **context).needs)
        return list(ret)

    @override
    def excludes(self, **context: Any) -> Sequence[Need]:
        ret = set()
        for workflow in current_oarepo_workflows.record_workflows:
            ret |= set(workflow.permissions(self._action, **context).excludes)
        return list(ret)

    @override
    def query_filter(self, **context: Any) -> dsl.query.Query:
        queries = query_filters_from_all_workflows(self._action, **context)
        return reduce(operator.or_, queries)


class FromRecordWorkflow(Generator):
    """Permission delegating check to workflow.

    The implementation of the permission gets the workflow id from the passed context
    (record or data) and then looks up the workflow definition in the configuration.
    If there is no workflow id on the record, the generator will return empty needs.
    If there is a workflow id on the record but there is no workflow definition for it,
    the generator will emit a warning and also return empty needs.

    The workflow definition must contain a permissions policy that is then used to
    determine the permissions for the action.
    """

    _action: str | Callable[..., str]

    def __init__(
        self,
        action: str | Callable[..., str],
        record_getter: Callable[..., Record] | None = None,
    ) -> None:
        """Initialize the permission.

        :param action: Action to check permissions for.
        :param record_getter: Callable to get the record from the context.
        """
        # might not be needed in subclasses
        super().__init__()
        self._action = action
        self._record_getter = record_getter

    def _action_name(self, **context: Any) -> str:
        """Get the action name from the context."""
        return self._action(**context) if callable(self._action) else self._action

    # noinspection PyMethodMayBeStatic
    def _get_workflow(self, record: Record | None = None, **context: Any) -> Workflow | None:
        """Get the workflow from the context.

        If the record is passed, the workflow is determined from the record.
        If the record is not passed, the workflow is determined from the input data.

        If the workflow is not found, a None is returned (for record) or default workflow
        (for data from the context).

        :param record: Record to get the workflow from.
        :param context: Context to get the workflow from.
        :return: Either the workflow or None if no workflow is defined on the record or is invalid.
        """
        if record:
            try:
                workflow = current_oarepo_workflows.get_workflow(record)
            except MissingWorkflowError:
                # no workflow on the record
                return None
            except InvalidWorkflowError as e:
                log.warning("Invalid workflow: %s", e)
                return None
        else:
            data = context.get("data", {})
            workflow_code = data.get("parent", {}).get("workflow", {})
            if not workflow_code:
                return current_oarepo_workflows.default_workflow
            if workflow_code not in current_oarepo_workflows.workflow_by_code:
                log.warning("Workflow %s does not exist in the configuration.", workflow_code)
                return None
            workflow = current_oarepo_workflows.workflow_by_code[workflow_code]
        return workflow

    def _get_permissions_from_workflow(
        self,
        record: Record | None = None,
        **context: Any,
    ) -> BaseWorkflowPermissionPolicy | None:
        """Get the permissions policy from the workflow.

        At first the workflow id is determined from the context.
        Then the permissions policy is determined from the workflow configuration,
        is instantiated with the action name and the context and the permissions
        for the action are returned.
        """
        if self._record_getter:
            record = self._record_getter(**context)
            # we should explicitly decide what should throw exception and what should not do anything
            if not record:
                return None
        action_name = self._action_name(**context)
        workflow = self._get_workflow(record, **context)
        policy = workflow.permissions(action_name, **context | {"record": record}) if workflow else None
        return policy if policy is not None and hasattr(policy, f"can_{action_name}") else None

    @override
    def needs(self, **context: Any) -> Sequence[Need]:
        """Return needs that are generated by the workflow permission."""
        policy = self._get_permissions_from_workflow(**context)
        if policy is not None:
            return policy.needs  # type: ignore[no-any-return]
        return []  # TODO: invenio adds disable if no generator

    @override
    def excludes(self, **context: Any) -> Sequence[Need]:
        """Return excludes that are generated by the workflow permission."""
        policy = self._get_permissions_from_workflow(**context)
        if policy is not None:
            return policy.excludes  # type: ignore[no-any-return]
        return []

    @override
    def query_filter(self, **context: Any) -> dsl.query.Query:
        """Return query filters that are generated by the workflow permission.

        Note: this implementation in fact will be called from WorkflowRecordPermissionPolicy.query_filters
        for each registered workflow type. The query_filters are then combined into a single query.
        """
        # query filters do not use reduce on the list
        policy = self._get_permissions_from_workflow(**context)
        if policy is not None:
            queries = policy.query_filters
            return reduce(operator.or_, queries) if queries else dsl.Q("match_none")
        return dsl.Q("match_none")


class WorkflowPermission(FromRecordWorkflow):
    """Deprecated alias for FromRecordWorkflow."""

    def __init__(self, action: str) -> None:
        """Initialize the generator."""
        import warnings

        warnings.warn(
            "WorkflowPermission is deprecated. Use FromRecordWorkflow instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(action)


class IfInState(RecipientGeneratorMixin, ConditionalGenerator):
    """Generator that checks if the record is in a specific state.

    If it is in the state, the then_ generators are used, otherwise the else_ generators are used.

    Example:
        .. code-block:: python

            can_edit = [
                IfInState("draft", [RecordOwners()])
            ]

    """

    def __init__(
        self,
        state: str | list[str] | tuple[str, ...],
        then_: Sequence[InvenioGenerator],
        else_: Sequence[InvenioGenerator] | None = None,
    ) -> None:
        """Initialize the generator."""
        if isinstance(state, str):
            state = [state]
        if not isinstance(state, list | tuple):
            raise TypeError(f"State must be a string, list or tuple. Got {type(state)}.")
        self.state = state
        super().__init__(then_, else_ or [])

    @override
    def _condition(self, record: Record, **context: Any) -> bool:  # type: ignore[reportIncompatibleMethodOverride]
        """Check if the record is in the state."""
        try:
            return record.state in self.state  # type: ignore[reportAttributeAccessIssue]
        except AttributeError:
            return False

    # TODO: 1. ConditionalGenerator is basically AggregateGenerator with _generators based on condition
    #       2. ReferenceReceivers could use some kind of aggregate mixin too; this is trivial
    #       3. Hot to solve reportArgumentType; record obviously can't be None though the mixin says it should
    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:
        from oarepo_workflows.requests.generators.multiple_entities import (
            MultipleEntitiesGenerator,
        )

        recipients = self.then_ if self._condition(record, **context) else self.else_  # type: ignore[reportArgumentType]
        generator = MultipleEntitiesGenerator(recipients)
        return generator.reference_receivers(record=record, request_type=request_type, **context)

    @override
    def _query_instate(self, **context: Any) -> dsl.query.Query:
        return dsl.Q("terms", state=self.state)

    def __repr__(self) -> str:
        """Return representation of the generator."""
        return f"IfInState({self.state}, then={self.then_!r}, else={self.else_!r})"

    def __str__(self) -> str:
        """Return string representation of the generator."""
        return repr(self)


class SameAs(InvenioSameAs):
    """Generator that delegates the permissions to another action.

    Example:
        .. code-block:: python
            class Perms:
                can_create_files = [
                    SameAs("can_edit_files")
                ]
                can_edit_files = [RecordOwners()]

    would mean that the permissions for creating files are the same as for editing files.
    This works even if you inherit from the class and override the can_edit_files.

    """

    def __init__(self, permission_name: str) -> None:
        """Emit a deprecation warning and delegate to Invenio's SameAs."""
        warnings.warn(
            "oarepo_workflows SameAs has been moved to invenio_records_permissions.generators.SameAs"
            " and will be removed in a future version. "
            "Use invenio_records_permissions.generators.SameAs directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(permission_name)


class UserWithRole(RecipientGeneratorMixin, Generator):
    """Generator that checks if the user has a specific role."""

    def __init__(self, role_name: str):
        """Initialize with the role name to check."""
        self.role_name = role_name

    @override
    def needs(self, **context: Any) -> Sequence[Need]:
        role = current_app.extensions["security"].datastore.find_role(self.role_name)
        if role is None:
            return []
        return [RoleNeed(role.id)]

    @override
    def query_filter(self, identity: Identity | None = None, **kwargs: Any) -> dsl.query.Query:
        if not identity:
            return dsl.Q("match_none")
        role = current_app.extensions["security"].datastore.find_role(self.role_name)
        if role is None:
            return dsl.Q("match_none")

        role_id = role.id
        for provide in identity.provides:
            if provide.method == "role" and provide.value == role_id:
                return dsl.Q("match_all")
        return dsl.Q("match_none")

    def __repr__(self) -> str:
        """Return representation of the generator."""
        return f"UserWithRole({self.role_name})"

    def __str__(self) -> str:
        """Return String representation of the generator."""
        return repr(self)

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:  # pragma: no cover
        role = current_app.extensions["security"].datastore.find_role(self.role_name)
        if role is None:
            return []
        return [{"group": role.id}]


class HasActionNeed(RecipientGeneratorMixin, Generator):
    """Generator that checks if the user has a specific action."""

    def __init__(self, action: str):
        """Initialize with the action to check."""
        self.action = action

    @override
    def needs(self, **context: Any) -> Sequence[Need]:
        return [ActionNeed(self.action)]

    def __repr__(self) -> str:
        """Return representation of the generator."""
        return f"HasActionNeed({self.action})"

    def __str__(self) -> str:
        """Return String representation of the generator."""
        return repr(self)

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:  # pragma: no cover
        return [{"action_need": self.action}]
