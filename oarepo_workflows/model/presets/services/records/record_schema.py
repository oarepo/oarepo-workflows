#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module providing workflow functionality for record schema.

This module defines a preset for extending record marshmallow schemas with workflow-related
fields, including state and state timestamp.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow as ma
from marshmallow_utils.fields import EDTFDateTimeString
from oarepo_model.customizations import AddMixins, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class WorkflowsRecordSchemaPreset(Preset):
    """Preset for record marshmallow schema."""

    modifies = ("RecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class StateSchemaMixin:
            state = ma.fields.String(dump_only=True)
            state_timestamp = EDTFDateTimeString(dump_only=True)

        yield AddMixins("RecordSchema", StateSchemaMixin)
