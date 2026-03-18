#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Tests for conditional generators."""

from __future__ import annotations

from invenio_records_permissions.generators import AuthenticatedUser
from invenio_requests.customizations.event_types import CommentEventType, LogEventType

from oarepo_workflows.requests.generators.conditionals import IfEventType


def test_if_event_type_condition_matches():
    """Test that IfEventType returns True when event_type matches."""
    generator = IfEventType(CommentEventType, [AuthenticatedUser()])

    assert generator._condition(event_type=CommentEventType) is True  # NOQA: SLF001


def test_if_event_type_condition_does_not_match():
    """Test that IfEventType returns False when event_type doesn't match."""
    generator = IfEventType(CommentEventType, [AuthenticatedUser()])

    assert generator._condition(event_type=LogEventType) is False  # NOQA: SLF001


def test_if_event_type_condition_no_event_type_passed():
    """Test that IfEventType returns False when event_type is not passed."""
    generator = IfEventType(CommentEventType, [AuthenticatedUser()])

    assert generator._condition() is False  # NOQA: SLF001
    assert generator._condition(event_type=None) is False  # NOQA: SLF001


def test_if_event_type_with_log_event():
    """Test IfEventType configured for LogEventType."""
    generator = IfEventType(LogEventType, [AuthenticatedUser()])

    assert generator._condition(event_type=LogEventType) is True  # NOQA: SLF001
    assert generator._condition(event_type=CommentEventType) is False  # NOQA: SLF001


def test_if_event_type_stores_correct_attributes():
    """Test that IfEventType stores the event_type correctly."""
    then_generators = [AuthenticatedUser()]
    else_generators = [AuthenticatedUser()]

    generator = IfEventType(CommentEventType, then_generators, else_=else_generators)

    assert generator.event_type == CommentEventType
    assert generator.then_ == then_generators
    assert generator.else_ == else_generators


def test_if_event_type_query_instate():
    """Test that _query_instate returns correct query."""
    generator = IfEventType(CommentEventType, [AuthenticatedUser()])

    query = generator._query_instate()  # NOQA: SLF001

    assert query.to_dict() == {"term": {"type_id": CommentEventType.type_id}}
