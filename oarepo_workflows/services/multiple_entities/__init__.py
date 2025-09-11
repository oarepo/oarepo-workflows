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

from invenio_records_resources.services.base.results import ServiceItemResult, ServiceListResult
from invenio_records_resources.services.base.service import Service
from invenio_requests.resolvers.registry import ResolverRegistry

from oarepo_workflows.resolvers.multiple_entities import MultipleEntitiesEntity, MultipleEntitiesResolver

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flask_principal import Identity
    from invenio_records_resources.references.entity_resolvers.base import EntityProxy
    from invenio_records_resources.services.base.config import ServiceConfig


def _serialize(entity: MultipleEntitiesEntity) -> dict[str, Any]:
    """Serialize entity to a dict."""
    ref = MultipleEntitiesResolver().reference_entity(entity)
    id_ = next(iter(ref.values()))
    return {"id": id_, "entities": json.loads(id_)}


class MultipleEntitiesResultItem(ServiceItemResult):
    """Single record result for multiple entities."""

    def __init__(
        self,
        entity: MultipleEntitiesEntity,
    ):
        """Override constructor to discard unnecesary arguments."""
        self._record = entity
        self._obj = entity

    @property
    def data(self) -> dict[str, Any]:
        """Get the record data.

        Returns:
            dict: The serialized record data.

        """
        return _serialize(self._record)


class MultipleEntitiesResultList(ServiceListResult):
    """List multiple entities result."""

    def __init__(self, results: list[MultipleEntitiesEntity]) -> None:
        """Override constructor to discard unnecesary arguments."""
        self._results = results

    @property
    def hits(self) -> Any:
        """Get iterator over search result hits.

        Yields:
            dict: The serialized record data for each hit.

        """
        for result in self._results:
            yield _serialize(result)


class MultipleEntitiesEntityService(Service):
    """Service implementation for multiple entities."""

    def __init__(self):
        """Override constructor to discard unnecesary arguments."""

    @property
    def config(self) -> ServiceConfig:
        """Get fake service config."""
        return cast("ServiceConfig", SimpleNamespace(service_id="multiple"))

    def read(self, identity: Identity, id_: str, **kwargs: Any) -> MultipleEntitiesResultItem:  # noqa ARG002
        """Return a service result item from multiple entity id.""" # todo multiple constant
        entity_proxy = ResolverRegistry.resolve_entity_proxy({"multiple": id_}, raise_=True)
        return MultipleEntitiesResultItem(entity=entity_proxy.resolve())

    def read_many(
        self,
        identity: Identity,  # noqa ARG002
        ids: Sequence[str],
        fields: Sequence[str] | None = None,  # noqa ARG002
        **kwargs: Any,  # noqa ARG002
    ) -> MultipleEntitiesResultList:
        """Return a service result list from multiple entity ids."""
        results = []
        if ids:
            expanded = [json.loads(id_) for id_ in ids]
            for exp in expanded:
                entities = [
                    cast("EntityProxy", ResolverRegistry.resolve_entity_proxy(ref_dict, raise_=True))
                    for ref_dict in exp
                ]
                results.append(MultipleEntitiesEntity(entities=entities))
        return MultipleEntitiesResultList(
            results=results,
        )
