#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
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
