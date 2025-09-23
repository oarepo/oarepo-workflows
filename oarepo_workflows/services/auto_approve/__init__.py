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

from typing import TYPE_CHECKING, Any

import marshmallow as ma
from invenio_records_resources.services.base.config import ServiceConfig
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from oarepo_runtime.services.config import EveryonePermissionPolicy
from oarepo_runtime.services.results import RecordItem

from oarepo_workflows.resolvers.auto_approve import AutoApprove
from oarepo_workflows.services.results import InMemoryResultList

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flask_principal import Identity
    from invenio_records_resources.services.base.results import ServiceListResult


class AutoApproveSchema(ma.Schema):
    """Marshmallow schema for auto-approve."""

    class Meta:
        """Marshmallow schema meta."""

        unknown = ma.INCLUDE

    id = ma.fields.String(dump_only=True)
    type = ma.fields.String(dump_only=True)


class AutoApproveServiceConfig(ServiceConfig):
    """Service configuration."""

    service_id = "auto_approve"
    permission_policy_cls = EveryonePermissionPolicy

    result_item_cls = RecordItem
    result_list_cls = InMemoryResultList
    record_cls = AutoApprove
    schema = AutoApproveSchema


class AutoApproveService(Service):
    """Service implementation for named entities.

    Provides concrete implementation of read operations for named entities
    that don't require database storage.
    """

    @property
    def schema(self) -> ServiceSchemaWrapper:
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    def read(self, identity: Identity, id_: str, **kwargs: Any) -> RecordItem:  # noqa ARG002
        """Read a single auto-approve record.

        Args:
            identity: The identity requesting access.
            id_: The record ID.
            **kwargs: Additional keyword arguments.

        Returns:
            ServiceItemResult: The auto-approve record.

        """
        return self.result_item(self, identity, AutoApprove(), schema=self.schema)

    def read_many(
        self,
        identity: Identity,
        ids: Sequence[str],  # noqa ARG002
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
        return self.result_list(identity, [AutoApprove()], self.schema)
