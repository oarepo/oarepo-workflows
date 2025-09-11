#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module providing search mapping configuration for workflow fields.

This module defines preset classes that configure search mappings for workflow-related
fields like state, state_timestamp, and parent workflow information in both draft and record
mappings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class WorkflowsMappingPreset(Preset):
    """Preset for record mapping."""

    modifies = ("draft-mapping",)  # depends on should already be finished?

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        workflow_mapping = {
            "mappings": {
                "properties": {
                    "state": {"type": "keyword", "ignore_above": 1024},
                    "state_timestamp": {
                        "type": "date",
                        "format": "strict_date_time||strict_date_time_no_millis||basic_date_time"
                        "||basic_date_time_no_millis||basic_date||strict_date||"
                        "strict_date_hour_minute_second||strict_date_hour_minute_second_fraction",
                    },
                    "parent": {
                        "properties": {
                            "workflow": {"type": "keyword", "ignore_above": 1024},
                        }
                    },
                }
            }
        }

        yield PatchJSONFile("draft-mapping", workflow_mapping)

        yield PatchJSONFile("record-mapping", workflow_mapping)
