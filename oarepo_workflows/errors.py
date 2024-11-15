#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Errors raised by oarepo-workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from marshmallow import ValidationError

if TYPE_CHECKING:
    from invenio_records_resources.records import Record


def _get_id_from_record(record: Record | dict) -> str:
    """Get the id from a record.

    :param record: A record or a dict representing a record.
    :return str: The id of the record.
    """
    # community record doesn't have id in dict form, only uuid
    return str(record["id"]) if "id" in record else str(record.id)


def _format_record(record: Record | dict) -> str:
    """Format a record for error messages.

    :param record: A record or a dict representing a record.
    :return str: A formatted string representing the record.
    """
    return f"{type(record).__name__}[{_get_id_from_record(record)}]"


class MissingWorkflowError(ValidationError):
    """Exception raised when a required workflow is missing."""

    def __init__(self, message: str, record: Record | dict | None = None) -> None:
        """Initialize the exception."""
        self.record = record
        if record:
            super().__init__(f"{message} Used on record {_format_record(record)}")
        else:
            super().__init__(message)


class InvalidWorkflowError(ValidationError):
    """Exception raised when a workflow is invalid."""

    def __init__(
        self,
        message: str,
        record: Record | dict | None = None,
        community_id: str = None,
    ) -> None:
        """Initialize the exception."""
        self.record = record
        if record:
            super().__init__(f"{message} Used on record {_format_record(record)}")
        elif community_id:
            super().__init__(f"{message} Used on community {community_id}")
        else:
            super().__init__(message)
