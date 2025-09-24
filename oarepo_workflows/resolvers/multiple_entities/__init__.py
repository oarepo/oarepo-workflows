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
from collections import defaultdict
from typing import TYPE_CHECKING, Any, cast, override

from invenio_records_resources.references.entity_resolvers import EntityProxy
from invenio_records_resources.references.entity_resolvers.base import EntityResolver
from invenio_records_resources.services.records.results import FieldsResolver
from invenio_requests.resolvers.registry import ResolverRegistry
from invenio_requests.services.results import EntityResolverExpandableField

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from flask_principal import Identity, Need


@dataclasses.dataclass
class MultipleEntitiesEntity:
    """Entity representing multiple entities.

    Implementation note: entities is intentionally list of EntityProxy and not list of resolved entities.
    The reason is that these are used to be converted to entity references and having proxy here makes it easier.
    """

    entities: list[EntityProxy]

    @classmethod
    def create_id(cls, entity_references: list[Mapping[str, str]]) -> str:
        """Create id from entity references."""
        entity_references.sort(key=lambda x: (next(iter(x.keys())), next(iter(x.values()))))
        return json.dumps(entity_references, sort_keys=True)

    @property
    def id(self) -> str:
        """Return id of the entity."""
        ref_dict_list = [entity.reference_dict for entity in self.entities]
        ref_dict_list.sort(key=lambda x: (next(iter(x.keys())), next(iter(x.values()))))
        return json.dumps(ref_dict_list, sort_keys=True)


class MultipleEntitiesProxy(EntityProxy):
    """Proxy for multiple-entities entity."""

    def _resolve(self) -> MultipleEntitiesEntity:
        """Resolve the entity reference into entity."""
        values = json.loads(self._parse_ref_dict_id())
        return MultipleEntitiesEntity(
            entities=[
                cast(
                    "EntityProxy",
                    ResolverRegistry.resolve_entity_proxy(ref, raise_=True),
                )
                for ref in values
            ]
        )

    @override
    def get_needs(self, ctx: dict | None = None) -> Sequence[Need]:
        """Get needs that the entity generate."""
        ret: list[Need] = []
        entity = self._entity if self._entity else self._resolve()
        for subentity_proxy in entity.entities:
            ret.extend(subentity_proxy.get_needs(ctx) or [])
        return ret

    @override
    def pick_resolved_fields(self, identity: Identity, resolved_dict: dict[str, Any]) -> dict[str, Any]:
        """Pick resolved fields for serialization of the entity to json."""
        entity_refs = json.loads(resolved_dict["id"])
        field_keys = []
        hit: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
        for entity_ref in entity_refs:
            type_ = next(iter(entity_ref.keys()))
            id_ = next(iter(entity_ref.values()))
            field_keys.append(f"{type_}.{id_}")
            hit[type_] |= {id_: {type_: id_}}
        fr = FieldsResolver([EntityResolverExpandableField(field_key) for field_key in field_keys])
        fr.resolve(identity, [hit])
        return fr.expand(identity, hit)  # type: ignore[no-any-return]


class MultipleEntitiesResolver(EntityResolver):
    """A resolver that resolves multiple entities entity."""

    # TODO: move as constant to MultipleEntitiesEntity? Would be similar to AutoApprove
    type_id = "multiple"

    def __init__(self) -> None:
        """Initialize the resolver."""
        super().__init__("multiple")

    @override
    def matches_reference_dict(self, ref_dict: dict) -> bool:
        """Check if the reference dictionary can be resolved by this resolver."""
        return cast("bool", self._parse_ref_dict_type(ref_dict) == self.type_id)

    @override
    def _reference_entity(self, entity: MultipleEntitiesEntity) -> dict[str, str]:
        """Return a reference dictionary for the entity."""
        return {self.type_id: entity.id}

    @override
    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity can be serialized to a reference by this resolver."""
        return isinstance(entity, MultipleEntitiesEntity)

    @override
    def _get_entity_proxy(self, ref_dict: dict) -> MultipleEntitiesProxy:
        """Get the entity proxy for the reference dictionary.

        Note: the proxy is returned to ensure the entity is loaded lazily, when needed.
        :param ref_dict: Reference dictionary.
        """
        return MultipleEntitiesProxy(self, ref_dict)
