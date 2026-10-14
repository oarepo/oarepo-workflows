# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module containing preset for adding workflow functionality to parent records.

This module defines a preset that adds workflow capabilities to parent records
in the Invenio model system by adding a workflow system field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    Customization,
    PrependMixin,
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

        yield PrependMixin(
            "ParentRecord",
            WorkflowsParentRecordMixin,
        )
