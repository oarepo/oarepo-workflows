#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service for reading multiple-recipients entities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import marshmallow as ma
from invenio_records_resources.services.base.config import ServiceConfig
from invenio_records_resources.services.records.results import (
    RecordBulkList,
    RecordItem,
    RecordList,
)
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from invenio_records_resources.services.records.service import RecordService
from invenio_requests.resolvers.registry import ResolverRegistry
from oarepo_runtime.services.config import EveryonePermissionPolicy

from oarepo_workflows.resolvers.multiple_entities import MultipleEntitiesEntity
from oarepo_workflows.services.results import InMemoryResultList

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_db.uow import UnitOfWork
    from invenio_records_resources.references.entity_resolvers.base import EntityProxy


class MultipleEntitiesSchema(ma.Schema):
    """Schema for multiple entities."""

    id = ma.fields.String()


class MultipleEntitiesEntityServiceConfig(ServiceConfig):
    # TODO: perhaps use a common superclass
    """Service configuration."""

    service_id = "multiple"
    permission_policy_cls = EveryonePermissionPolicy

    result_item_cls = RecordItem
    result_list_cls = InMemoryResultList
    record_cls = MultipleEntitiesEntity
    schema = MultipleEntitiesSchema


class MultipleEntitiesEntityService(RecordService):
    """Service implementation for multiple entities."""

    config: MultipleEntitiesEntityServiceConfig

    @property
    def schema(self) -> ServiceSchemaWrapper:
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    @override
    def read(
        self,
        identity: Identity,
        id_: str,
        expand: bool = False,
        action: str | None = None,
        **kwargs: Any,
    ) -> RecordItem:
        """Return a service result item from multiple entity id."""
        entity_proxy = cast(
            "EntityProxy",
            ResolverRegistry.resolve_entity_proxy({"multiple": id_}, raise_=True),
        )
        return self.result_item(self, identity, entity_proxy.resolve(), schema=self.schema)

    @override
    def read_many(
        self,
        identity: Identity,
        ids: list[str],
        fields: list[str] | None = None,
        **kwargs: Any,
    ) -> RecordList:
        """Return a service result list from multiple entity ids."""
        results = [
            cast(
                "EntityProxy",
                ResolverRegistry.resolve_entity_proxy({"multiple": id_}, raise_=True),
            ).resolve()
            for id_ in ids
        ]
        # TODO: I would guess we need our own typed service superclass ig but why is it complaining
        #  here and not in read or in AutoApproveService?
        return self.result_list(identity, results, self.schema)  # type: ignore[no-any-return]

    #
    # High-level API
    #
    @override
    def search(
        self,
        identity: Identity,
        params: dict[str, Any] | None = None,
        search_preference: str | None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:
        """Search for records matching the querystring."""
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover

    @override
    def scan(
        self,
        identity: Identity,
        params: dict[str, Any] | None = None,
        search_preference: None = None,
        expand: bool = False,
        **kwargs: Any,
    ) -> RecordList:
        """Scan for records matching the querystring."""
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover

    @override
    def reindex(
        self,
        identity: Identity,
        params: dict[str, Any] | None = None,
        search_preference: str | None = None,
        search_query: Any | None = None,
        extra_filter: Any | None = None,
        **kwargs: Any,
    ) -> bool:
        """Reindex records matching the query parameters."""
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover

    @override
    def create(
        self,
        identity: Identity,
        data: dict[str, Any],
        uow: UnitOfWork | None = None,
        expand: bool = False,
    ) -> RecordItem:
        """Create a record.

        :param identity: Identity of user creating the record.
        :param data: Input data according to the data schema.
        """
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover

    @override
    def exists(self, identity: Identity, id_: str) -> bool:
        """Check if the record exists and user has permission."""
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover

    @override
    def read_all(
        self,
        identity: Identity,
        fields: list[str],
        max_records: int = 150,
        **kwargs: Any,
    ) -> RecordList:
        """Search for records matching the querystring."""
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover

    @override
    def update(
        self,
        identity: Identity,
        id_: str,
        data: dict[str, Any],
        revision_id: int | None = None,
        uow: UnitOfWork | None = None,
        expand: bool = False,
    ) -> RecordItem:
        """Replace a record."""
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover

    @override
    def delete(
        self,
        identity: Identity,
        id_: str,
        revision_id: int | None = None,
        uow: UnitOfWork | None = None,
    ) -> bool:
        """Delete a record from database and search indexes."""
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover

    @override
    def rebuild_index(self, identity: Identity, uow: UnitOfWork | None = None) -> bool:
        """Reindex all records managed by this service.

        Note: Skips (soft) deleted records.
        """
        return True

    #
    # notification handlers
    #
    @override
    def on_relation_update(
        self,
        identity: Identity,
        record_type: str,
        records_info: list[Any],
        notif_time: str,
        limit: int = 100,
    ) -> bool:
        """Handle the update of a related field record.

        :param identity: the identity that will search and reindex.
        :param record_type: the record type with relations.
        :param records_info: a list of tuples containing (recid, uuid, revision_id)
                             for each record to reindex.
        :param notif_time: reindex records index before this time.
        :param limit: reindex in chunks of these records. The limit must be lower than
                      the search engine maxClauseCount setting.
        :returns: True.
        """
        return True

    @override
    def create_or_update_many(
        self,
        identity: Identity,
        data: list[tuple[str, dict[str, Any]]],
        uow: UnitOfWork | None = None,
    ) -> RecordBulkList:
        """Create or update a list of records.

        This method takes a list of record data and creates or updates the corresponding records.

        :param identity: The user identity performing the operation.
        :param data: A list of tuples containing the record ID and record data.
        :param uow: The unit of work to register the record operations. Defaults to None.
        """
        raise NotImplementedError("Not applicable for multiple entities service")  # pragma: no cover
