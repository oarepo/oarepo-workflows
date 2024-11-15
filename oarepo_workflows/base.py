#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Support any workflows on Invenio record."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, Protocol

from . import WorkflowRecordPermissionPolicy
from .requests import WorkflowRequestPolicy
from .services.permissions import DefaultWorkflowPermissions

if TYPE_CHECKING:
    from flask_babel import LazyString
    from flask_principal import Identity
    from invenio_records_resources.records import Record
    from invenio_records_resources.services.uow import UnitOfWork


@dataclasses.dataclass
class Workflow:
    """A workflow definition."""

    label: str | LazyString
    """A human-readable label for the workflow."""

    permission_policy_cls: type[DefaultWorkflowPermissions]
    """A permission policy class that handles permissions on records that are governed by this workflow."""

    request_policy_cls: type[WorkflowRequestPolicy] = WorkflowRequestPolicy
    """A request policy class that defines which requests can be applied to records governed by this workflow."""

    def permissions(self, action: str, **over: Any) -> DefaultWorkflowPermissions:
        """Return permission policy for this workflow applicable to the given action.

        :param  action:      action for which permission is asked
        """
        return self.permission_policy_cls(action, **over)

    def requests(self) -> WorkflowRequestPolicy:
        """Return instance of request policy for this workflow."""
        return self.request_policy_cls()

    def __post_init__(self) -> None:
        """Check that the classes are subclasses of the expected classes.

        This is just a sanity check to raise an error as soon as possible.
        """
        assert not issubclass(
            self.permission_policy_cls, WorkflowRecordPermissionPolicy
        )
        assert issubclass(self.permission_policy_cls, DefaultWorkflowPermissions)
        assert issubclass(self.request_policy_cls, WorkflowRequestPolicy)


class StateChangedNotifier(Protocol):
    """A protocol for a state change notifier.

    State changed notifier is a callable that is called when a state of a record changes,
    for example as a result of a workflow transition.
    """

    def __call__(
        self,
        identity: Identity,
        record: Record,
        previous_state: str,
        new_state: str,
        *args: Any,
        uow: UnitOfWork,
        **kwargs: Any,
    ):
        """Notify about a state change.

        :param identity:        identity of the user who initiated the state change
        :param record:          record whose state changed
        :param previous_state:  previous state of the record
        :param new_state:       new state of the record
        :param args:            additional arguments
        :param uow:             unit of work
        :param kwargs:          additional keyword arguments
        """
        ...


class WorkflowChangeNotifier(Protocol):
    """A protocol for a workflow change notifier.

    Workflow changed notifier is a callable that is called
    when a workflow of a record changes.
    """

    def __call__(
        self,
        identity: Identity,
        record: Record,
        previous_workflow_id: str,
        new_workflow_id: str,
        *args: Any,
        uow: UnitOfWork,
        **kwargs: Any,
    ):
        """Notify about a workflow change.

        :param identity:                identity of the user who initiated the workflow change
        :param record:                  record whose workflow changed
        :param previous_workflow_id:    previous workflow of the record
        :param new_workflow_id:         new workflow of the record
        :param args:                    additional arguments
        :param uow:                     unit of work
        :param kwargs:                  additional keyword arguments
        """
        ...
