#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service for reading ActionNeed entities.

The implementation is simple as ActionNeed is resolved directly from its value (action name)
so there is no need to store it to database/fetch it from the database.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow as ma
from flask_principal import Need
from invenio_access import ActionNeed
from invenio_records_resources.services.records.config import RecordServiceConfig
from invenio_records_resources.services.records.results import (
    RecordBulkList,
    RecordItem,
    RecordList,
)
from invenio_records_resources.services.records.service import RecordService
from oarepo_runtime.services.config import EveryonePermissionPolicy

from oarepo_workflows.services.results import InMemoryResultList

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_db.uow import UnitOfWork


class ActionNeedSchema(ma.Schema):
    """Marshmallow schema for ActionNeed.

    Serializes ``ActionNeed(value)`` as ``{"id": value, "type": "action_need"}``.
    """

    class Meta:
        """Marshmallow schema meta."""

        unknown = ma.INCLUDE

    id = ma.fields.String(attribute="value", dump_only=True)
    type = ma.fields.String(dump_default="action_need")


class ActionNeedServiceConfig(RecordServiceConfig):
    """Service configuration for ActionNeed service."""

    service_id = "action_need"
    permission_policy_cls = EveryonePermissionPolicy

    result_item_cls = RecordItem
    result_list_cls = InMemoryResultList
    record_cls = Need
    schema = ActionNeedSchema


class ActionNeedService(RecordService):
    """Service implementation for ActionNeed entities.

    Provides read operations for ``invenio_access.ActionNeed`` entities.
    The ActionNeed is the entity itself (similar to how User is the entity
    in invenio_users_resources); no separate wrapper class is required.
    """

    @override
    def read(
        self,
        identity: Identity,
        id_: str,
        expand: bool = False,
        action: str | None = None,
        **kwargs: Any,
    ) -> RecordItem:
        """Read a single ActionNeed record by action name.

        Args:
            identity: The identity requesting access.
            id_: The action name (e.g. ``"administration"``).
            expand: Whether to expand the record.
            action: Permission action performed.
            **kwargs: Additional keyword arguments.

        Returns:
            RecordItem: The ActionNeed wrapped in a service result item.

        """
        return self.result_item(self, identity, ActionNeed(id_), schema=self.schema)

    @override
    def read_many(
        self,
        identity: Identity,
        ids: list[str],
        fields: list[str] | None = None,
        **kwargs: Any,
    ) -> RecordList:
        """Read multiple ActionNeed records by action names.

        Args:
            identity: The identity requesting access.
            ids: Iterable of action names.
            fields: Optional fields to include in the result.
            **kwargs: Additional keyword arguments.

        Returns:
            RecordList: List of ActionNeed records.

        """
        return self.result_list(identity, [ActionNeed(id_) for id_ in ids], self.schema)

    #
    # High-level API — not applicable for ActionNeed service
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
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover

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
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover

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
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover

    @override
    def create(
        self,
        identity: Identity,
        data: dict[str, Any],
        uow: UnitOfWork | None = None,
        expand: bool = False,
    ) -> RecordItem:
        """Create a record."""
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover

    @override
    def exists(self, identity: Identity, id_: str) -> bool:
        """Check if the record exists and user has permission."""
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover

    @override
    def read_all(
        self,
        identity: Identity,
        fields: list[str],
        max_records: int = 150,
        **kwargs: Any,
    ) -> RecordList:
        """Search for records matching the querystring."""
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover

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
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover

    @override
    def delete(
        self,
        identity: Identity,
        id_: str,
        revision_id: int | None = None,
        uow: UnitOfWork | None = None,
    ) -> bool:
        """Delete a record from database and search indexes."""
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover

    @override
    def rebuild_index(self, identity: Identity, uow: UnitOfWork | None = None) -> bool:
        """Reindex all records managed by this service."""
        return True

    @override
    def on_relation_update(
        self,
        identity: Identity,
        record_type: str,
        records_info: list[Any],
        notif_time: str,
        limit: int = 100,
    ) -> bool:
        """Handle the update of a related field record."""
        return True

    @override
    def create_or_update_many(
        self,
        identity: Identity,
        data: list[tuple[str, dict[str, Any]]],
        uow: UnitOfWork | None = None,
    ) -> RecordBulkList:
        """Create or update a list of records."""
        raise NotImplementedError("Not applicable for action-need service")  # pragma: no cover
