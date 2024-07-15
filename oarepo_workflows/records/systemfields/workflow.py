from invenio_db import db
from invenio_records.systemfields.model import ModelField
from oarepo_runtime.records.systemfields import MappingSystemFieldMixin

from ...proxies import current_oarepo_workflows


class WorkflowField(MappingSystemFieldMixin, ModelField):

    def __init__(self):
        self._workflow = None  # added in db
        super().__init__(model_field_name="workflow", key="workflow")

    def post_create(self, parent_record):
        if not parent_record.workflow:
            parent_record.workflow = current_oarepo_workflows.get_default_workflow(record=parent_record)

    def pre_commit(self, parent_record):
        super().pre_commit(parent_record)

    @property
    def mapping(self):
        return {
            self.attr_name: {
                "type": "keyword"
            }
        }