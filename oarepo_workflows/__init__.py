#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Support any workflows on Invenio record."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from oarepo_workflows.services.permissions import (
    FromRecordWorkflow,
    IfInState,
    WorkflowPermission,
    WorkflowRecordPermissionPolicyMixin,
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

try:
    __version__ = version("oarepo-workflows")
except PackageNotFoundError:
    __version__ = "0.0.0dev0+unknown"


__all__ = (
    "AutoApprove",
    "AutoRequest",
    "FromRecordWorkflow",
    "IfInState",
    "Workflow",
    "WorkflowPermission",
    "WorkflowRecordPermissionPolicyMixin",
    "WorkflowRequest",
    "WorkflowRequestEscalation",
    "WorkflowRequestPolicy",
    "WorkflowTransitions",
    "current_oarepo_workflows",
)
