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
from .proxies import current_oarepo_workflows
from .requests import (
    AutoApprove,
    AutoRequest,
    WorkflowRequest,
    WorkflowRequestEscalation,
    WorkflowRequestPolicy,
    WorkflowTransitions,
)

__version__ = "2.0.0dev2"
"""Version of the library."""


__all__ = (
    "AutoApprove",
    "AutoRequest",
    "FromRecordWorkflow",
    "IfInState",
    "Workflow",
    "WorkflowPermission",
    "WorkflowRecordPermissionPolicy",
    "WorkflowRequest",
    "WorkflowRequestEscalation",
    "WorkflowRequestPolicy",
    "WorkflowTransitions",
    "current_oarepo_workflows",
)
