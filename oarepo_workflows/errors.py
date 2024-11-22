#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Errors raised by oarepo-workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from marshmallow import ValidationError

if TYPE_CHECKING:
    from invenio_records_resources.records import Record


def _get_id_from_record(record: Record | dict) -> str:
    """Get the id from a record.

    :param record: A record or a dict representing a record.
    :return str: The id of the record.
    """
    # community record doesn't have id in dict form, only uuid
    try:
        if "id" in record:
            return str(record["id"])
    except TypeError:
        pass
    if hasattr(record, "id"):
        return str(record.id)
    return str(record)


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
        community_id: Optional[str] = None,
    ) -> None:
        """Initialize the exception."""
        self.record = record
        if record:
            super().__init__(f"{message} Used on record {_format_record(record)}")
        elif community_id:
            super().__init__(f"{message} Used on community {community_id}")
        else:
            super().__init__(message)


class InvalidConfigurationError(Exception):
    """Exception raised when a configuration is invalid."""


class EventTypeNotInWorkflow(Exception):
    """Exception raised when user tries to create a request with a request type that is not defined in the workflow."""

    def __init__(self, request_type: str, event_type: str, workflow_code: str) -> None:
        """Initialize the exception."""
        self.request_type = request_type
        self.workflow = workflow_code
        self.event_type = event_type

    @property
    def description(self) -> str:
        """Exception's description."""
        return f"Event type {self.event_type} is not on request type {self.request_type} in workflow {self.workflow}."


class RequestTypeNotInWorkflow(Exception):
    """Exception raised when user tries to create a request with a request type that is not defined in the workflow."""

    def __init__(self, request_type: str, workflow_code: str) -> None:
        """Initialize the exception."""
        self.request_type = request_type
        self.workflow = workflow_code

    @property
    def description(self) -> str:
        """Exception's description."""
        return f"Request type {self.request_type} not in workflow {self.workflow}."
