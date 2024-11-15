from __future__ import annotations
from invenio_records.systemfields.base import SystemField
from oarepo_runtime.records.systemfields import MappingSystemFieldMixin

from typing import Self

class RecordStateField(MappingSystemFieldMixin, SystemField):
    def __init__(self, key: str="state", initial: str="draft", config=None) -> None:
        self._config = config
        self._initial = initial
        super().__init__(key=key)

    def post_create(self, record) -> None:
        self.set_dictkey(record, self._initial)

    def post_init(self, record, data, model=None, **kwargs) -> None:
        if not record.state:
            self.set_dictkey(record, self._initial)

    def __get__(self, record, owner=None) -> str | Self:
        """Get the persistent identifier."""
        if record is None:
            return self
        return self.get_dictkey(record)

    def __set__(self, record, value) -> None:
        self.set_dictkey(record, value)

    @property
    def mapping(self) -> dict[str, dict[str, str]]:
        return {self.attr_name: {"type": "keyword"}}
