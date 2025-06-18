#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Conditional generators based on request and event types."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

from invenio_records_permissions.generators import ConditionalGenerator, Generator

if TYPE_CHECKING:
    from invenio_requests.customizations import EventType, RequestType


class IfRequestTypeBase(abc.ABC, ConditionalGenerator):
    """Base class for conditional generators that generate needs based on request type."""

    def __init__(
        self, request_types: list[str] | tuple[str] | str, then_: list[Generator]
    ) -> None:
        """Initialize the generator."""
        super().__init__(then_, else_=[])
        if not isinstance(request_types, (list, tuple)):
            request_types = [request_types]
        self.request_types = request_types


class IfRequestType(IfRequestTypeBase):
    """Conditional generator that generates needs when a current request is of a given type."""

    def _condition(self, request_type: RequestType, **kwargs: Any) -> bool:
        return request_type.type_id in self.request_types


class IfEventType(ConditionalGenerator):
    """Conditional generator that generates needs when a current event is of a given type."""

    def __init__(
        self,
        event_types: list[str] | tuple[str] | str,
        then_: list[Generator],
        else_: list[Generator] | None = None,
    ) -> None:
        """Initialize the generator."""
        else_ = [] if else_ is None else else_
        super().__init__(then_, else_=else_)
        if not isinstance(event_types, (list, tuple)):
            event_types = [event_types]
        self.event_types = event_types

    def _condition(self, event_type: EventType, **kwargs: Any) -> bool:
        return event_type.type_id in self.event_types

class PrivilegedRole(ConditionalGenerator):
    """Generator that checks if the record has no edit draft."""

    def __init__(
        self, role:Generator, read: bool=False, update: bool=False, action_accept: bool=False, action_decline: bool=False,
            events:list[str] | None = None
    ) -> None:
        """Initialize the generator."""
        self._role = role
        self._actions = set()
        if read:
            self._actions.add("read")
        if update:
            self._actions.add("update")
        if action_accept:
            self._actions.add("action_accept")
        if action_decline:
            self._actions.add("action_decline")
        self._events = events
        super().__init__(then_=[self._role], else_=[])

    def _condition(self, action: str, **kwargs) -> bool:
        return action in self._actions
