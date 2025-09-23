#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service for reading multiple-recipients entities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import marshmallow as ma
from invenio_records_resources.services.base.config import ServiceConfig
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from invenio_requests.resolvers.registry import ResolverRegistry
from oarepo_runtime.services.config import EveryonePermissionPolicy
from oarepo_runtime.services.results import RecordItem

from oarepo_workflows.resolvers.multiple_entities import MultipleEntitiesEntity
from oarepo_workflows.services.results import InMemoryResultList

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flask_principal import Identity
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


class MultipleEntitiesEntityService(Service):
    """Service implementation for multiple entities."""

    @property
    def schema(self) -> ServiceSchemaWrapper:
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    def read(self, identity: Identity, id_: str, **kwargs: Any) -> RecordItem:  # noqa ARG002
        """Return a service result item from multiple entity id."""
        entity_proxy = cast(
            "EntityProxy",
            ResolverRegistry.resolve_entity_proxy({"multiple": id_}, raise_=True),
        )
        return self.result_item(self, identity, entity_proxy.resolve(), schema=self.schema)

    def read_many(
        self,
        identity: Identity,
        ids: Sequence[str],
        fields: Sequence[str] | None = None,  # noqa ARG002
        **kwargs: Any,  # noqa ARG002
    ) -> InMemoryResultList:
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
