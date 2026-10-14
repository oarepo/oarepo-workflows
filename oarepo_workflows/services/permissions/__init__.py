# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Permissions for workflows."""

from __future__ import annotations

from .generators import FromRecordWorkflow, IfInState, IfRDMRecordPassed, WorkflowPermission
from .record_permission_policy import WorkflowRecordPermissionPolicyMixin
from .workflow_permissions import (
    BaseWorkflowPermissionPolicy,
    DefaultWorkflowPermissions,
)

__all__ = (
    "BaseWorkflowPermissionPolicy",
    "DefaultWorkflowPermissions",
    "FromRecordWorkflow",
    "IfInState",
    "IfRDMRecordPassed",
    "WorkflowPermission",
    "WorkflowRecordPermissionPolicyMixin",
)
