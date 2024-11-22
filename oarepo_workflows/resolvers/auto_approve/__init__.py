#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Auto approve entity and resolver."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_records_resources.references.entity_resolvers import EntityProxy
from invenio_records_resources.references.entity_resolvers.base import EntityResolver

if TYPE_CHECKING:
    from flask_principal import Identity, Need


class AutoApproveEntity:
    """Entity representing auto approve."""


class AutoApproveProxy(EntityProxy):
    """Proxy for auto approve entity."""

    def _resolve(self) -> AutoApproveEntity:
        """Resolve the entity reference into entity."""
        return AutoApproveEntity()

    def get_needs(self, ctx: dict | None = None) -> list[Need]:
        """Get needs that the entity generate."""
        return []  # grant_tokens calls this

    def pick_resolved_fields(self, identity: Identity, resolved_dict: dict) -> dict:
        """Pick resolved fields for serialization of the entity to json."""
        return {"auto_approve": resolved_dict["id"]}


class AutoApproveResolver(EntityResolver):
    """A resolver that resolves auto approve entity."""

    type_id = "auto_approve"

    def __init__(self) -> None:
        """Initialize the resolver."""
        super().__init__("auto_approve")

    def matches_reference_dict(self, ref_dict: dict) -> bool:
        """Check if the reference dictionary can be resolved by this resolver."""
        return self._parse_ref_dict_type(ref_dict) == self.type_id

    def _reference_entity(self, entity: Any) -> dict[str, str]:
        """Return a reference dictionary for the entity."""
        return {self.type_id: "true"}

    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity can be serialized to a reference by this resolver."""
        return isinstance(entity, AutoApproveEntity)

    def _get_entity_proxy(self, ref_dict: dict) -> AutoApproveProxy:
        """Get the entity proxy for the reference dictionary.

        Note: the proxy is returned to ensure the entity is loaded lazily, when needed.
        :param ref_dict: Reference dictionary.
        """
        return AutoApproveProxy(self, ref_dict)
