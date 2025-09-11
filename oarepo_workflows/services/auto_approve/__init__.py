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

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

from invenio_records_resources.services.base.results import ServiceItemResult, ServiceListResult
from invenio_records_resources.services.base.service import Service

from oarepo_workflows.resolvers.auto_approve import AutoApprove
import marshmallow as ma
if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from flask_principal import Identity
    from invenio_records_resources.services.base.config import ServiceConfig

class AutoApproveSchema(ma.Schema):
    class Meta:
        unknown = ma.INCLUDE

class AutoApproveRecordList(ServiceListResult):
    """List autopprove result."""


    @property
    def hits(self) -> Generator[dict[str, Any], None, None]:
        """Get iterator over search result hits.

        Yields:
            dict: The serialized record data for each hit.

        """

        yield AutoApprove.serialization

    def __len__(self):
        """Return the total numer of hits."""
        return 1

    def __iter__(self):
        """Iterator over the hits."""
        return iter(self.hits)

    def to_dict(self):
        return {"hits": {"total": 1, "hits": list(self.hits)}}

class AutoApproveServiceConfig(ServiceConfig):
    """Service configuration."""
    service_id = "auto_approve"
    permission_policy_cls = EveryonePermissionPolicy

    result_item_cls = RecordItem
    result_list_cls = AutoApproveRecordList

class AutoApproveService(Service):
    """Service implementation for named entities.

    Provides concrete implementation of read operations for named entities
    that don't require database storage.
    """

    def read(self, identity: Identity, id_: str, **kwargs: Any) -> ServiceItemResult:  # noqa ARG002
        """Read a single auto-approve record.

        Args:
            identity: The identity requesting access.
            id_: The record ID.
            **kwargs: Additional keyword arguments.

        Returns:
            ServiceItemResult: The auto-approve record.

        """
        return self.result_item(self, identity, AutoApprove(), schema=AutoApproveSchema())

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
        return self.result_list()
