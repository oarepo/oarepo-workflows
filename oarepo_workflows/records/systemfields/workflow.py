from invenio_records.systemfields.model import ModelField
from oarepo_runtime.records.systemfields import MappingSystemFieldMixin

from ...proxies import current_oarepo_workflows


class WorkflowField(MappingSystemFieldMixin, ModelField):

    def __init__(self):
        self._workflow = None  # added in db
        super().__init__(model_field_name="workflow", key="workflow")

    @property
    def mapping(self):
        return {self.attr_name: {"type": "keyword"}}
