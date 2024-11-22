#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Requests layer."""

from __future__ import annotations

from .generators import AutoApprove, AutoRequest, RecipientGeneratorMixin
from .policy import (
    WorkflowRequestPolicy,
)
from .requests import (
    RecipientEntityReference,
    WorkflowRequest,
    WorkflowRequestEscalation,
    WorkflowTransitions,
)

__all__ = (
    "WorkflowRequestPolicy",
    "RecipientEntityReference",
    "WorkflowRequest",
    "WorkflowRequestEscalation",
    "WorkflowTransitions",
    "AutoApprove",
    "AutoRequest",
    "RecipientGeneratorMixin",
)
