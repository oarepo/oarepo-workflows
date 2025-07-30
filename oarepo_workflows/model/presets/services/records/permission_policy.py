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

from oarepo_runtime.services.config import EveryonePermissionPolicy

from oarepo_model.customizations import Customization, ChangeBase
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset
from oarepo_workflows.services.permissions.record_permission_policy import WorkflowRecordPermissionPolicy

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class WorkflowsPermissionPolicyPreset(Preset):
    """
    Preset for record service class.
    """

    modifies = ["PermissionPolicy"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        yield ChangeBase("PermissionPolicy", EveryonePermissionPolicy, WorkflowRecordPermissionPolicy, subclass=True)
