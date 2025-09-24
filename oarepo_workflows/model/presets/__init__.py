#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Collection of workflow presets for configuring record models and services.

This module provides presets that handle different aspects of workflow-enabled records,
including draft support, service components, permissions, and schema definitions.
"""

from __future__ import annotations

from oarepo_workflows.model.presets.records.draft_record import WorkflowsDraftPreset
from oarepo_workflows.model.presets.records.parent_record import (
    WorkflowsParentRecordPreset,
)
from oarepo_workflows.model.presets.records.parent_record_metadata import (
    WorkflowsParentRecordMetadataPreset,
)
from oarepo_workflows.model.presets.records.record import WorkflowsRecordPreset
from oarepo_workflows.model.presets.records.workflows_mapping import (
    WorkflowsMappingPreset,
)
from oarepo_workflows.model.presets.services.records.parent_record_schema import (
    WorkflowsParentRecordSchemaPreset,
)
from oarepo_workflows.model.presets.services.records.permission_policy import (
    WorkflowsPermissionPolicyPreset,
)
from oarepo_workflows.model.presets.services.records.record_schema import (
    WorkflowsRecordSchemaPreset,
)
from oarepo_workflows.model.presets.services.records.service_config import (
    WorkflowsServiceConfigPreset,
)

workflows_preset = [
    WorkflowsDraftPreset,
    WorkflowsParentRecordPreset,
    WorkflowsRecordPreset,
    WorkflowsParentRecordMetadataPreset,
    WorkflowsPermissionPolicyPreset,
    WorkflowsParentRecordSchemaPreset,
    WorkflowsMappingPreset,
    WorkflowsRecordSchemaPreset,
    WorkflowsServiceConfigPreset,
]
