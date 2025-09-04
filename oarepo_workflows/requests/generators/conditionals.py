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
from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.services.generators import ConditionalGenerator, Generator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invenio_requests.customizations import EventType, RequestType


class IfRequestTypeBase(abc.ABC, ConditionalGenerator):
    """Base class for conditional generators that generate needs based on request type."""

    def __init__(self, request_types: Sequence[str] | str, then_: Sequence[Generator]) -> None:
        """Initialize the generator."""
        super().__init__(then_, else_=[])
        if isinstance(request_types, str):
            request_types = [request_types]
        self.request_types = request_types


class IfRequestType(IfRequestTypeBase):
    """Conditional generator that generates needs when a current request is of a given type."""

    @override
    def _condition(self, request_type: RequestType, **kwargs: Any) -> bool:
        return request_type.type_id in self.request_types


class IfEventType(ConditionalGenerator):
    """Conditional generator that generates needs when a current event is of a given type."""

    def __init__(
        self,
        event_types: Sequence[str] | str,
        then_: Sequence[Generator],
        else_: Sequence[Generator] | None = None,
    ) -> None:
        """Initialize the generator."""
        else_ = [] if else_ is None else else_
        super().__init__(then_, else_=else_)
        if isinstance(event_types, str):
            event_types = [event_types]
        self.event_types = event_types

    @override
    def _condition(self, event_type: EventType, **kwargs: Any) -> bool:  # type: ignore[reportIncompatibleMethodOverride]
        return event_type.type_id in self.event_types
