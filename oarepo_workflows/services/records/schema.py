#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Mixin for records with workflow support."""

from __future__ import annotations

import marshmallow as ma
from invenio_drafts_resources.services.records.schema import ParentSchema


class WorkflowParentSchema(ParentSchema):
    """Schema for parent record with workflow support."""

    workflow = ma.fields.String()
