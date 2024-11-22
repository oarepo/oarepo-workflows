#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Record layer, system fields."""

from .state import RecordStateField, RecordStateTimestampField
from .workflow import WorkflowField

__all__ = (
    "RecordStateField",
    "WorkflowField",
    "RecordStateTimestampField",
)
