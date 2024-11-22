#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Model mixins."""

from __future__ import annotations

from invenio_db import db
from sqlalchemy import String


class RecordWorkflowParentModelMixin:
    """Mixin for a ParentRecord database model that adds a workflow field."""

    workflow = db.Column(String)
    """Workflow identifier."""
