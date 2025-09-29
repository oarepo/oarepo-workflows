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
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    Self,
    cast,
    overload,
    override,
)

from invenio_records_resources.records.api import Record
from oarepo_runtime.records.systemfields import TypedSystemField

if TYPE_CHECKING:
    from invenio_records.models import RecordMetadataBase


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


class RecordStateField(TypedSystemField[Record, str]):
    """State system field."""

    def __init__(self, key: str = "state", initial: str = "draft") -> None:
        """Initialize the state field."""
        self._initial = initial
        super().__init__(key=key)

    def post_create(self, record: Record) -> None:
        """Set the initial state when record is created."""
        self.set_dictkey(record, self._initial)

    # field_data
    @override
    def post_init(
        self,
        record: Record,
        data: dict[str, Any] | None = None,
        model: RecordMetadataBase | None = None,
        **kwargs: Any,
    ) -> None:
        """Set the initial state when record is created."""
        state = self.get_dictkey(record)
        if not state:
            self.set_dictkey(record, self._initial)

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, instance: Record, owner: type | None = None) -> str: ...

    def __get__(self, instance: Record | None, owner: type | None = None) -> str | Self:
        """Get the persistent identifier."""
        if instance is None:
            return self
        return cast("str", self.get_dictkey(instance))

    @overload
    def __set__(self, instance: None, value: Self) -> None: ...

    @overload
    def __set__(self, instance: Record, value: str) -> None: ...

    # TODO: why pyright thinks this is an override error?
    def __set__(self, instance: Record | None, value: str | Self) -> None:  # type: ignore[override]
        """Directly set the state of the record."""
        if instance is None or isinstance(value, RecordStateField):
            raise AttributeError("Cannot set state on class or with another field.")
        if self.get_dictkey(instance) != value:
            self.set_dictkey(instance, value)
            instance["state_timestamp"] = datetime.now(tz=UTC).isoformat()


class RecordStateTimestampField(TypedSystemField[Record, str]):
    """State system field."""

    def __init__(self, key: str = "state_timestamp") -> None:
        """Initialize the state field."""
        super().__init__(key=key)

    def post_create(self, record: Record) -> None:
        """Set the initial state when record is created."""
        self.set_dictkey(record, datetime.now(tz=UTC).isoformat())

    @override
    def post_init(
        self,
        record: Record,
        data: dict[str, Any] | None = None,
        model: RecordMetadataBase | None = None,
        **kwargs: Any,
    ) -> None:
        """Set the initial state when record is created."""
        state_timestamp = self.get_dictkey(record)
        if not state_timestamp:
            self.set_dictkey(record, datetime.now(tz=UTC).isoformat())

    @overload
    def __get__(self, record: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, record: Record, owner: type | None = None) -> str: ...

    def __get__(self, record: Record | None, owner: type | None = None) -> str | None | Self:
        """Get the persistent identifier."""
        if record is None:
            return self
        return cast("str | None", self.get_dictkey(record))
