#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""State system field."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional, Protocol, Self, cast, overload

from invenio_records.systemfields.base import SystemField
from oarepo_runtime.records.systemfields import MappingSystemFieldMixin


class WithState(Protocol):
    """A protocol for a record containing a state field.

    Later on, if typing.Intersection is implemented,
    one could use it to have the record correctly typed as
    record: Intersection[WithState, Record]
    """

    state: str
    """State of the record."""

    state_timestamp: datetime
    """Timestamp of the last state change."""


class RecordStateField(MappingSystemFieldMixin, SystemField):
    """State system field."""

    def __init__(self, key: str = "state", initial: str = "draft") -> None:
        """Initialize the state field."""
        self._initial = initial
        super().__init__(key=key)

    def post_create(self, record: WithState) -> None:
        """Set the initial state when record is created."""
        self.set_dictkey(record, self._initial)

    def post_init(
        self, record: WithState, data: dict, model: Optional[Any] = None, **kwargs: Any
    ) -> None:
        """Set the initial state when record is created."""
        if not record.state:
            self.set_dictkey(record, self._initial)

    @overload
    def __get__(self, record: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, record: WithState, owner: type | None = None) -> str: ...

    def __get__(
        self, record: WithState | None, owner: type | None = None
    ) -> str | Self:
        """Get the persistent identifier."""
        if record is None:
            return self
        return self.get_dictkey(record)

    def __set__(self, record: WithState, value: str) -> None:
        """Directly set the state of the record."""
        if self.get_dictkey(record) != value:
            self.set_dictkey(record, value)
            cast(dict, record)["state_timestamp"] = datetime.now(tz=UTC).isoformat()

    @property
    def mapping(self) -> dict[str, dict[str, str]]:
        """Return the opensearch mapping for the state field."""
        return {
            self.attr_name: {"type": "keyword"},
        }


class RecordStateTimestampField(MappingSystemFieldMixin, SystemField):
    """State system field."""

    def __init__(self, key: str = "state_timestamp") -> None:
        """Initialize the state field."""
        super().__init__(key=key)

    def post_create(self, record: WithState) -> None:
        """Set the initial state when record is created."""
        self.set_dictkey(record, datetime.now(tz=UTC).isoformat())

    def post_init(
        self, record: WithState, data: dict, model: Optional[Any] = None, **kwargs: Any
    ) -> None:
        """Set the initial state when record is created."""
        if not record.state_timestamp:
            self.set_dictkey(record, datetime.now(tz=UTC).isoformat())

    @overload
    def __get__(self, record: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, record: WithState, owner: type | None = None) -> str: ...

    def __get__(
        self, record: WithState | None, owner: type | None = None
    ) -> str | Self:
        """Get the persistent identifier."""
        if record is None:
            return self
        return self.get_dictkey(record)

    @property
    def mapping(self) -> dict[str, dict[str, str]]:
        """Return the opensearch mapping for the state field."""
        # not needed as oarepo-model-builder-workflows already generated this field into the mapping
        return {
            self.attr_name: {
                "type": "date",
                "format": "strict_date_time||strict_date_time_no_millis||"
                "basic_date_time||basic_date_time_no_millis||"
                "basic_date||strict_date||"
                "strict_date_hour_minute_second||strict_date_hour_minute_second_fraction",
            },
        }
