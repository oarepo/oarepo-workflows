#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Multiple entities entity and resolver."""

from __future__ import annotations

import dataclasses
import json
from typing import TYPE_CHECKING, Any

from invenio_records_resources.references.entity_resolvers import EntityProxy
from invenio_records_resources.references.entity_resolvers.base import EntityResolver
from invenio_requests.resolvers.registry import ResolverRegistry

if TYPE_CHECKING:
    from flask_principal import Identity, Need


@dataclasses.dataclass
class MultipleEntitiesEntity:
    """Entity representing multiple entities."""

    entities: list[EntityProxy]


class MultipleEntitiesProxy(EntityProxy):
    """Proxy for multiple-entities entity."""

    def _resolve(self) -> MultipleEntitiesEntity:
        """Resolve the entity reference into entity."""
        values = json.loads(self._parse_ref_dict_id())
        return MultipleEntitiesEntity(
            entities=[
                ResolverRegistry.resolve_entity_proxy(ref, raise_=True)  # type: ignore
                for ref in values
            ]
        )

    def get_needs(self, ctx: dict | None = None) -> list[Need]:
        """Get needs that the entity generate."""
        ret = []
        for entity in self._resolve().entities:
            ret.extend(entity.get_needs(ctx) or [])
        return ret

    def pick_resolved_fields(self, identity: Identity, resolved_dict: dict) -> dict:
        """Pick resolved fields for serialization of the entity to json."""
        return {"multiple": resolved_dict["id"]}


class MultipleEntitiesResolver(EntityResolver):
    """A resolver that resolves multiple entities entity."""

    type_id = "multiple"

    def __init__(self) -> None:
        """Initialize the resolver."""
        super().__init__("multiple")

    def matches_reference_dict(self, ref_dict: dict) -> bool:
        """Check if the reference dictionary can be resolved by this resolver."""
        return self._parse_ref_dict_type(ref_dict) == self.type_id

    def _reference_entity(self, entity: MultipleEntitiesEntity) -> dict[str, str]:
        """Return a reference dictionary for the entity."""
        print("!!!! multiple_entities/__init__.py _reference_entity", entity.entities)
        return {
            self.type_id: json.dumps([part.reference_dict for part in entity.entities])
        }

    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity can be serialized to a reference by this resolver."""
        return isinstance(entity, MultipleEntitiesEntity)

    def _get_entity_proxy(self, ref_dict: dict) -> MultipleEntitiesProxy:
        """Get the entity proxy for the reference dictionary.

        Note: the proxy is returned to ensure the entity is loaded lazily, when needed.
        :param ref_dict: Reference dictionary.
        """
        return MultipleEntitiesProxy(self, ref_dict)
