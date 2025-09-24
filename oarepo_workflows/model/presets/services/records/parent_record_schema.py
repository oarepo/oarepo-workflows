#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module providing schema preset for parent record workflows.

This module defines a preset that adds workflow-related marshmallow fields
to parent record schemas, allowing serialization and validation of workflow
data through schema fields in parent records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow as ma
from oarepo_model.customizations import AddMixins, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class WorkflowsParentRecordSchemaPreset(Preset):
    """Preset for parent record marshmallow schema."""

    modifies = ("ParentRecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class WorkflowSchemaMixin:
            workflow = ma.fields.String()

        yield AddMixins("ParentRecordSchema", WorkflowSchemaMixin)
