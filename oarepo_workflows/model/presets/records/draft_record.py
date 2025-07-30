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

from invenio_drafts_resources.records import Draft as InvenioDraft
from invenio_rdm_records.records.systemfields import HasDraftCheckField
from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.systemfields import IndexField
from oarepo_runtime.records.systemfields.record_status import RecordStatusSystemField

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset
from oarepo_workflows.records.systemfields.state import RecordStateField, RecordStateTimestampField

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class WorkflowsDraftPreset(Preset):
    """
    Preset for Draft record.
    """

    modifies = [
        "Draft",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
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
