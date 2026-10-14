# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Record layer, system fields."""

from __future__ import annotations

from .state import RecordStateField, RecordStateTimestampField
from .workflow import WorkflowField

__all__ = (
    "RecordStateField",
    "RecordStateTimestampField",
    "WorkflowField",
)
