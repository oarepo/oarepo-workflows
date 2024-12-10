#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Definition of workflow permissions."""

from __future__ import annotations

from typing import Any

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AuthenticatedUser,
    Disable,
    SystemProcess,
)
from oarepo_runtime.services.permissions import RecordOwners

from .generators import IfInState, SameAs


class DefaultWorkflowPermissions(RecordPermissionPolicy):
    """Base class for workflow permissions, subclass from it and put the result to Workflow constructor.

    Example:
        class MyWorkflowPermissions(DefaultWorkflowPermissions):
            can_read = [AnyUser()]
    in invenio.cfg
    WORKFLOWS = {
        'default': Workflow(
            permission_policy_cls = MyWorkflowPermissions, ...
        )
    }

    """

    # TODO: new version - update; edit current version - disable -> idk if there's other way than something like IfNoEditDraft/IfNoNewVersionDraft generators-

    files_edit = [
        IfInState("draft", [RecordOwners()]),
        IfInState("published", [Disable()]),
    ]

    system_process = SystemProcess()

    def __init__(self, action_name: str | None = None, **over: Any) -> None:
        """Initialize the workflow permissions."""
        can = getattr(self, f"can_{action_name}")
        if self.system_process not in can:
            can.append(self.system_process)
        over["policy"] = self
        super().__init__(action_name, **over)

    can_read = [
        IfInState("draft", [RecordOwners()]),
        IfInState("published", [AuthenticatedUser()]),
    ]
    can_update = [IfInState("draft", [RecordOwners()])]
    can_delete = [
        IfInState("draft", [RecordOwners()]),
    ]
    can_create = [AuthenticatedUser()]
    can_publish = [AuthenticatedUser()]
    can_new_version = [AuthenticatedUser()]

    can_create_files = [SameAs("files_edit")]
    can_set_content_files = [SameAs("files_edit")]
    can_commit_files = [SameAs("files_edit")]
    can_update_files = [SameAs("files_edit")]
    can_delete_files = [SameAs("files_edit")]
    can_draft_create_files = [SameAs("files_edit")]
    can_read_files = [SameAs("can_read")]
    can_get_content_files = [SameAs("can_read")]
    can_list_files = [SameAs("can_read")]

    can_read_draft = [SameAs("can_read")]
    can_update_draft = [SameAs("can_update")]
    can_delete_draft = [SameAs("can_delete")]
