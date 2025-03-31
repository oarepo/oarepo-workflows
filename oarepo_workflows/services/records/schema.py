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
from invenio_rdm_records.services.schemas.parent import RDMParentSchema

class WorkflowParentSchema(ParentSchema):
    """Schema for parent record with workflow support."""

    workflow = ma.fields.String()

class RDMWorkflowParentSchema(RDMParentSchema):
    """RDM based schema for parent record with workflow support."""

    workflow = ma.fields.String()
