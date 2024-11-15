#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

import marshmallow as ma
from invenio_drafts_resources.services.records.schema import ParentSchema


class WorkflowParentSchema(ParentSchema):
    workflow = ma.fields.String()
