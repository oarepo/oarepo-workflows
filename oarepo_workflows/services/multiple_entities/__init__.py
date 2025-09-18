#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service for reading multiple-recipients entities."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import marshmallow as ma
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.base.config import ServiceConfig
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from invenio_requests.resolvers.registry import ResolverRegistry
from oarepo_runtime.services.config import EveryonePermissionPolicy
from oarepo_runtime.services.results import RecordItem

from oarepo_workflows.resolvers.auto_approve import AutoApprove
from oarepo_workflows.resolvers.multiple_entities import MultipleEntitiesEntity, MultipleEntitiesResolver
from oarepo_workflows.services.results import FakeHits, FakeResults, InMemoryResultList

# from oarepo_workflows.services.auto_approve import InMemoryResultList

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flask_principal import Identity
    from invenio_records_resources.references.entity_resolvers.base import EntityProxy


class MultipleEntitiesSchema(ma.Schema):
    id = ma.fields.String()

    @ma.post_dump
    def serialize_entities(self, data, many, **kwargs) -> None:
        multiple_entity = self.context["record"] # == instantiated entity from the result list; is it always in here?
        identity = self.context["identity"]
        # TODO: does this even makes sense with all types of entities?
        projections = []
        for entity_proxy in multiple_entity.entities:
            service = current_service_registry.get(entity_proxy._resolver._service_id)
            entity_schema = service.schema  # is there a possible service with no schema? fallback?
            entity = entity_proxy.resolve()
            projection = (
                entity_schema.dump(  # this won't work on Users - User entity is not UserAggregate used in service
                    # this would only really work if we made special entity-service record mapping in config
                    entity,
                    context={
                        "identity": identity,
                        "record": entity,
                    },
                )
            )
            projections.append(projection)
        data["entities"] = projections


class MultipleEntitiesEntityServiceConfig(ServiceConfig):
    # TODO: i still think there should be superclass for these two (for now) services
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
    def schema(self):
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    def read(self, identity: Identity, id_: str, **kwargs: Any) -> RecordItem:  # noqa ARG002
        """Return a service result item from multiple entity id."""
        entity_proxy = ResolverRegistry.resolve_entity_proxy({"multiple": id_}, raise_=True)
        return self.result_item(self, identity, entity_proxy.resolve(), schema=self.schema)

    def read_many(
        self,
        identity: Identity,
        ids: Sequence[str],
        fields: Sequence[str] | None = None,  # noqa ARG002
        **kwargs: Any,  # noqa ARG002
    ) -> InMemoryResultList:
        """Return a service result list from multiple entity ids."""
        results = [ResolverRegistry.resolve_entity_proxy({"multiple": id_}, raise_=True).resolve() for id_ in ids]
        return self.result_list(self, identity, FakeResults(FakeHits(results)))
