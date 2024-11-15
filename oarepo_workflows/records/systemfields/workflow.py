from __future__ import annotations

from invenio_records.systemfields.model import ModelField
from oarepo_runtime.records.systemfields import MappingSystemFieldMixin


class WorkflowField(MappingSystemFieldMixin, ModelField):

    def __init__(self) -> None:
        self._workflow = None  # added in db
        super().__init__(model_field_name="workflow", key="workflow")

    @property
    def mapping(self) -> dict[str, dict[str, str]]:
        return {self.attr_name: {"type": "keyword"}}
