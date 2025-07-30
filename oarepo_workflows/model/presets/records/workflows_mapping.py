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

from oarepo_model.customizations import CopyFile, Customization, PatchJSONFile
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class WorkflowsMappingPreset(Preset):
    """
    Preset for record service class.
    """

    modifies = ["draft-mapping"] # depends on should already be finished?

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        parent_mapping = {
            "mappings": {
                "properties": {
                    "state": {
                        "type": "keyword",
                        "ignore_above": 1024
                    },
                    "state_timestamp": {
                        "type": "date",
                        "format": "strict_date_time||strict_date_time_no_millis||basic_date_time||basic_date_time_no_millis||basic_date||strict_date||strict_date_hour_minute_second||strict_date_hour_minute_second_fraction"
                    },
                    "parent": {
                        "properties": {
                            "workflow": {"type": "keyword", "ignore_above": 1024},
                            "workflow-change-notifier-called": {"type": "boolean"},
                        }
                    },
                }
            }
        }

        yield PatchJSONFile("draft-mapping", parent_mapping)

        yield PatchJSONFile("record-mapping", parent_mapping)
