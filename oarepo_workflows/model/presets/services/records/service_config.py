#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module providing service configuration preset for workflow functionality.

This module contains preset class that configures record service by adding
workflow component to handle workflow-related operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    AddToList,
    Customization,
)
from oarepo_model.presets import Preset

from oarepo_workflows.services.components.workflow import WorkflowComponent

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class WorkflowsServiceConfigPreset(Preset):
    """Preset for workflows service config."""

    modifies = ("record_service_components",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToList("record_service_components", WorkflowComponent)
