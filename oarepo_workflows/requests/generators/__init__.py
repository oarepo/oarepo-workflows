#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
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
