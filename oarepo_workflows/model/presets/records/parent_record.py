#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module containing preset for adding workflow functionality to parent records.

This module defines a preset that adds workflow capabilities to parent records
in the Invenio model system by adding a workflow system field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

from oarepo_workflows.records.systemfields.workflow import WorkflowField

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class WorkflowsParentRecordPreset(Preset):
    """Preset that modifies a ParentRecord class."""

    modifies = ("ParentRecord",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class WorkflowsParentRecordMixin:
            """Base class for parent records in the model."""

            workflow = WorkflowField()

        yield AddMixins(
            "ParentRecord",
            WorkflowsParentRecordMixin,
        )
