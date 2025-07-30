from oarepo_workflows.model.presets.records.draft_record import WorkflowsDraftPreset
from oarepo_workflows.model.presets.records.parent_record import WorkflowsParentRecordPreset
from oarepo_workflows.model.presets.records.parent_record_metadata import WorkflowsParentRecordMetadataPreset
from oarepo_workflows.model.presets.records.record import WorkflowsRecordPreset
from oarepo_workflows.model.presets.records.workflows_mapping import WorkflowsMappingPreset
from oarepo_workflows.model.presets.services.records.parent_record_schema import WorkflowsParentRecordSchemaPreset
from oarepo_workflows.model.presets.services.records.permission_policy import WorkflowsPermissionPolicyPreset
from oarepo_workflows.model.presets.services.records.record_schema import WorkflowsRecordSchemaPreset
from oarepo_workflows.model.presets.services.records.service_config import RequestsServiceConfigPreset

workflows_presets = [WorkflowsDraftPreset, WorkflowsParentRecordPreset, WorkflowsRecordPreset,
                     RequestsServiceConfigPreset, WorkflowsParentRecordMetadataPreset, WorkflowsPermissionPolicyPreset,
                     WorkflowsParentRecordSchemaPreset, WorkflowsMappingPreset, WorkflowsRecordSchemaPreset]