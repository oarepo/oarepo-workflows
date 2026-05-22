#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""ActionNeed resolver."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from flask_principal import Identity, ItemNeed, Need
from invenio_access import ActionNeed
from invenio_records_resources.references.entity_resolvers import EntityProxy
from invenio_records_resources.references.entity_resolvers.base import EntityResolver

if TYPE_CHECKING:
    from collections.abc import Mapping


class ActionNeedProxy(EntityProxy):
    """Proxy for ActionNeed entity."""

    def _resolve(self) -> Need:
        """Resolve the entity reference into entity."""
        return ActionNeed(self._parse_ref_dict_id())

    @override
    def get_needs(self, ctx: dict | None = None) -> list[Need | ItemNeed]:
        """Get needs that the entity generate."""
        return [self._resolve()]

    @override
    def pick_resolved_fields(self, identity: Identity, resolved_dict: Mapping[str, str]) -> dict[str, str]:
        """Pick resolved fields for serialization of the entity to json."""
        return cast("dict[str, str]", self.reference_dict)


class ActionNeedResolver(EntityResolver):
    """A resolver that resolves action need entity."""

    type_id = "action_need"

    def __init__(self) -> None:
        """Initialize the resolver."""
        super().__init__("action_need")

    @override
    def matches_reference_dict(self, ref_dict: dict) -> bool:
        """Check if the reference dictionary can be resolved by this resolver."""
        return len(ref_dict) == 1 and self.type_id in ref_dict

    @override
    def _reference_entity(self, entity: Any) -> dict[str, str]:
        """Return a reference dictionary for the entity."""
        return {self.type_id: entity.value}

    @override
    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity can be serialized to a reference by this resolver."""
        return isinstance(entity, Need) and entity.method == "action"

    @override
    def _get_entity_proxy(self, ref_dict: dict) -> ActionNeedProxy:
        """Get the entity proxy for the reference dictionary.

        Note: the proxy is returned to ensure the entity is loaded lazily, when needed.
        :param ref_dict: Reference dictionary.
        """
        return ActionNeedProxy(self, ref_dict)
