#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator
from oarepo_model.customizations import Customization, AddMixins
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset
import marshmallow as ma
from oarepo_runtime.services.schema.validation import validate_datetime

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class WorkflowsRecordSchemaPreset(Preset):
    """
    Preset for record service class.
    """

    modifies = ["RecordSchema"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class StateSchemaMixin:
            state = ma.fields.String(dump_only=True)

            state_timestamp = ma.fields.String(dump_only=True, validate=[validate_datetime])

        yield AddMixins("RecordSchema", StateSchemaMixin)