#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module providing permission policy for workflow records.

This module defines a preset for changing base permission policy class
for records to WorkflowRecordPermissionPolicy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_permissions.policies.records import RecordPermissionPolicy
from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.presets import Preset

from oarepo_workflows.services.permissions.record_permission_policy import (
    WorkflowRecordPermissionPolicy,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class WorkflowsPermissionPolicyPreset(Preset):
    """Preset for workflow permissions class."""

    modifies = ("PermissionPolicy",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase(
            "PermissionPolicy",
            RecordPermissionPolicy,
            WorkflowRecordPermissionPolicy,
            subclass=True,
        )
