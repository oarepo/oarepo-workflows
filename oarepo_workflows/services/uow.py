#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Unit of Work operations module for workflows.

Provides operation class for changing the workflow state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_records_resources.services.uow import Operation, RecordCommitOp, UnitOfWork
from oarepo_runtime.proxies import current_runtime

from oarepo_workflows.proxies import current_oarepo_workflows

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.records.api import Record


class StateChangeOperation(Operation):
    """Unit of Work operation for changing the state of a record."""

    def __init__(
        self,
        identity: Identity,
        record: Record,
        new_state: str,
        *extra_args: Any,
        commit_record: bool = True,
        notify_later: bool = False,
        **extra_kwargs: Any,
    ):
        """Initialize the operation with the record and the new state."""
        self.identity = identity
        self.record = record
        self.previous_value = cast("str", getattr(record, "state", ""))
        self.new_state = new_state
        self.commit = commit_record
        self.notify_later = notify_later
        self.extra_args = extra_args
        self.extra_kwargs = extra_kwargs
        super().__init__()

    @override
    def on_register(self, uow: UnitOfWork) -> None:
        """Change the state of the record and commit the changes."""
        self.record.state = self.new_state  # type: ignore[assignment]

        if self.commit:
            service = current_runtime.get_record_service_for_record(self.record)
            uow.register(RecordCommitOp(self.record, indexer=service.indexer))

        # If we do not notify later, run the notifications immediately
        if not self.notify_later:
            self.run_notifications(uow)

    @override
    def on_post_commit(self, uow: UnitOfWork) -> None:
        """Run notifications after the commit."""
        if self.notify_later:
            # note: we need to run this in a separate unit of work, as notification
            # handlers might register a commit operation and as we are already in
            # post commit in this uow, it would never get executed.
            with UnitOfWork() as uow1:
                self.run_notifications(uow1)
                uow1.commit()

    def run_notifications(self, uow: UnitOfWork) -> None:
        """Run state change notification actions after the commit."""
        for state_changed_notifier in current_oarepo_workflows.state_changed_notifiers:
            state_changed_notifier(
                self.identity,
                self.record,
                self.previous_value,
                self.new_state,
                *self.extra_args,
                uow=uow,
                **self.extra_kwargs,
            )
