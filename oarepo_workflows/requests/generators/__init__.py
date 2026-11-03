# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Need generators."""

from __future__ import annotations

from .auto import AutoApprove, auto_approve_need, auto_request_need
from .conditionals import IfEventType
from .recipient_generator import RecipientGeneratorMixin

__all__ = (
    "AutoApprove",
    "IfEventType",
    "RecipientGeneratorMixin",
    "auto_approve_need",
    "auto_request_need",
)
