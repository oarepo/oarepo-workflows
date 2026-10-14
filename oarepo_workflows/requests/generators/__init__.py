# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Need generators."""

from __future__ import annotations

from .auto import AutoApprove, AutoRequest, auto_approve_need, auto_request_need
from .conditionals import IfEventType
from .recipient_generator import RecipientGeneratorMixin

__all__ = (
    "AutoApprove",
    "AutoRequest",
    "IfEventType",
    "RecipientGeneratorMixin",
    "auto_approve_need",
    "auto_request_need",
)
