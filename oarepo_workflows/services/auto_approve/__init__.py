#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service for reading auto-approve entities.

The implementation is simple as auto approve is just one entity
so there is no need to store it to database/fetch it from the database.
"""

from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

from invenio_records_resources.services.base.results import ServiceItemResult, ServiceListResult
from invenio_records_resources.services.base.service import Service

from oarepo_workflows.resolvers.auto_approve import AutoApprove

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.services.base.config import ServiceConfig
    from invenio_records_resources.services.base.results import (
        ServiceItemResult,
        ServiceListResult,
    )


class AutoApproveRecordItem(ServiceItemResult):
    """Single record result for AutoApprove."""

    def __init__(
        self,
    ):
        """Override constructor to discard unnecesary arguments."""
        self._record = AutoApprove()

    @property
    def data(self) -> dict[str, str]:
        """Get the record data.

        Returns:
            dict: The serialized record data.

        """
        return AutoApprove.serialization


class AutoApproveRecordList(ServiceListResult):
    """List autopprove result."""

    def __init__(
        self,
        results: list[AutoApprove],
    ) -> None:
        """Override constructor to discard unnecesary arguments."""
        self._results = results
        self._params = None

    @property
    def total(self) -> int:
        """Get total number of hits."""
        return len(self._results)

    @property
    def hits(self) -> Any:
        """Get iterator over search result hits.

        Yields:
            dict: The serialized record data for each hit.

        """
        for _ in self._results:
            yield AutoApprove.serialization


class AutoApproveService(Service):
    """Service implementation for named entities.

    Provides concrete implementation of read operations for named entities
    that don't require database storage.
    """

    def __init__(self):
        """Override constructor to discard unnecesary arguments."""

    @property
    def config(self) -> ServiceConfig:
        """Get fake service config."""
        return cast("ServiceConfig", SimpleNamespace(service_id="auto_approve"))

    def read(self, identity: Identity, id_: str, **kwargs: Any) -> ServiceItemResult:  # noqa ARG002
        """Read a single auto-approve record.

        Args:
            identity: The identity requesting access.
            id_: The record ID.
            **kwargs: Additional keyword arguments.

        Returns:
            ServiceItemResult: The auto-approve record.

        """
        return AutoApproveRecordItem()

    def read_many(
        self,
        identity: Identity,  # noqa ARG002
        ids: Sequence[str],
        fields: Sequence[str] | None = None,  # noqa ARG002
        **kwargs: Any,  # noqa ARG002
    ) -> ServiceListResult:
        """Read multiple auto-approve records.

        Args:
            identity: The identity requesting access.
            ids: Iterable of record IDs.
            fields: Optional fields to include in the result.
            **kwargs: Additional keyword arguments.

        Returns:
            ServiceListResult: List of auto-approve records.

        """
        return AutoApproveRecordList([AutoApprove() for _ in ids])
