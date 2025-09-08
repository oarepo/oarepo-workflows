#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Conditional generators based on request and event types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from oarepo_runtime.services.generators import ConditionalGenerator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invenio_records_permissions.generators import Generator as InvenioGenerator
    from invenio_requests.customizations import EventType


class IfEventType(ConditionalGenerator):
    """Conditional generator that generates needs when a current event is of a given type."""

    def __init__(
        self,
        event_type: type[EventType],
        then_: Sequence[InvenioGenerator],
        else_: Sequence[InvenioGenerator] | None = None,
    ) -> None:
        """Initialize the generator."""
        else_ = [] if else_ is None else else_
        super().__init__(then_, else_=else_)
        self.event_type = event_type

    @override
    def _condition(self, event_type: type[EventType], **kwargs: Any) -> bool:  # type: ignore[reportIncompatibleMethodOverride]
        return cast("bool", event_type == self.event_type)
