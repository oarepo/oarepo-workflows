# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset module for parent record metadata in workflow functionality.

This module provides preset customizations for parent record metadata classes,
adding workflow-specific functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from oarepo_model.customizations import (
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset
from sqlalchemy import String

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class WorkflowsParentRecordMetadataPreset(Preset):
    """Preset that modifies a ParentRecordMetadata class."""

    modifies = ("ParentRecordMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClassField("ParentRecordMetadata", "workflow", db.Column(String))
