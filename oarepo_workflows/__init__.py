#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Support any workflows on Invenio record."""

from __future__ import annotations

from oarepo_workflows.services.permissions import (
    FromRecordWorkflow,
    IfInState,
    WorkflowPermission,
    WorkflowRecordPermissionPolicy,
)

from .base import Workflow
from .requests import (
    AutoApprove,
    AutoRequest,
    WorkflowRequest,
    WorkflowRequestEscalation,
    WorkflowRequestPolicy,
    WorkflowTransitions,
)

__all__ = (
    "IfInState",
    "Workflow",
    "WorkflowPermission",
    "WorkflowRecordPermissionPolicy",
    "WorkflowRequestPolicy",
    "WorkflowRequest",
    "WorkflowRequestEscalation",
    "WorkflowTransitions",
    "FromRecordWorkflow",
    "AutoApprove",
    "AutoRequest",
)
