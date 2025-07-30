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
from oarepo_model.customizations import (
    AddMixins,
    AddToDictionary,
    AddToList,
    ChangeBase,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset
from oarepo_workflows.services.components.workflow import WorkflowComponent

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder

class RequestsServiceConfigPreset(Preset):
    """
    Preset for record service config class.
    """

    modifies = [
        "record_service_components_before"
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        yield AddToList("record_service_components_before", WorkflowComponent, prepend=True)

