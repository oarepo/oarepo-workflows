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
from typing import TYPE_CHECKING, Any, Protocol, Self, cast, overload, override

from invenio_records.systemfields.base import SystemField

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


class RecordStateField(SystemField):
    """State system field."""

    def __init__(self, key: str = "state", initial: str = "draft") -> None:
        """Initialize the state field."""
        self._initial = initial
        super().__init__(key=key)

    def post_create(self, record: WithState) -> None:
        """Set the initial state when record is created."""
        self.set_dictkey(record, self._initial)

    # field_data
    @override
    def post_init(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        record: WithState,
        data: dict[str, Any] | None = None,
        model: RecordMetadataBase | None = None,
        **kwargs: Any,
    ) -> None:
        """Set the initial state when record is created."""
        if not record.state:
            self.set_dictkey(record, self._initial)

    @overload
    def __get__(self, record: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, record: WithState, owner: type | None = None) -> str: ...

    def __get__(self, record: WithState | None, owner: type | None = None) -> str | Self:
        """Get the persistent identifier."""
        if record is None:
            return self  # type: ignore[no-any-return]
        return self.get_dictkey(record)  # type: ignore[no-any-return]

    # Ignore because superclass always causes exception so the correct return type is NoReturn
    def __set__(self, record: WithState, value: str) -> None:  # type: ignore[reportIncompatibleMethodOverride]
        """Directly set the state of the record."""
        if self.get_dictkey(record) != value:
            self.set_dictkey(record, value)
            cast("dict", record)["state_timestamp"] = datetime.now(tz=UTC).isoformat()


class RecordStateTimestampField(SystemField):
    """State system field."""

    def __init__(self, key: str = "state_timestamp") -> None:
        """Initialize the state field."""
        super().__init__(key=key)

    def post_create(self, record: WithState) -> None:
        """Set the initial state when record is created."""
        self.set_dictkey(record, datetime.now(tz=UTC).isoformat())

    @override
    def post_init(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        record: WithState,
        data: dict[str, Any] | None = None,
        model: RecordMetadataBase | None = None,
        **kwargs: Any,
    ) -> None:
        """Set the initial state when record is created."""
        if not record.state_timestamp:
            self.set_dictkey(record, datetime.now(tz=UTC).isoformat())

    @overload
    def __get__(self, record: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, record: WithState, owner: type | None = None) -> str: ...

    def __get__(self, record: WithState | None, owner: type | None = None) -> str | Self:
        """Get the persistent identifier."""
        if record is None:
            return self  # type: ignore[no-any-return]
        return self.get_dictkey(record)  # type: ignore[no-any-return]
