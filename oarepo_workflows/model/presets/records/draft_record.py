#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module providing workflow functionality for draft records.

This module contains preset classes that add workflow state tracking
capabilities to draft records, including state and timestamp tracking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

from oarepo_workflows.records.systemfields.state import (
    RecordStateField,
    RecordStateTimestampField,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class WorkflowsDraftPreset(Preset):
    """Preset for Draft record."""

    modifies = ("Draft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class WorkflowsDraftMixin:
            """Base class for records in the model.

            This class extends InvenioRecord and can be customized further.
            """

            state = RecordStateField()
            state_timestamp = RecordStateTimestampField()

        yield AddMixins(
            "Draft",
            WorkflowsDraftMixin,
        )
