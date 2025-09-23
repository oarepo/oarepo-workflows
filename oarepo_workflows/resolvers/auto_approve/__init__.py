#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Auto approve entity and resolver."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.references.entity_resolvers import EntityProxy
from invenio_records_resources.references.entity_resolvers.base import EntityResolver

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from flask_principal import Identity, Need


class AutoApprove:
    """Entity representing auto approve."""

    id = "true"
    type = "auto_approve"
    # TODO: see below
    # ref_dict = MappingProxyType({"auto_approve": "true"}) - must be dict due to how
    # invenio_records_resources.references.registry.ResolverRegistryBase.reference_entity is implemented

    # for mypy ref_dict: ClassVar[dict[str, str]] = {"auto_approve": "true"}

    # Instead of ClassVar; typing for classproperty does not work

    # idea: define reference dict type

    ref_dict: Mapping[str, str] = {"auto_approve": "true"}


class AutoApproveProxy(EntityProxy):
    """Proxy for auto approve entity."""

    def _resolve(self) -> AutoApprove:
        """Resolve the entity reference into entity."""
        return AutoApprove()

    @override
    def get_needs(self, ctx: dict | None = None) -> Sequence[Need]:
        """Get needs that the entity generate."""
        return []  # grant_tokens calls this

    @override
    def pick_resolved_fields(self, identity: Identity, resolved_dict: Mapping[str, str]) -> Mapping[str, str]:
        """Pick resolved fields for serialization of the entity to json."""
        return AutoApprove.ref_dict


class AutoApproveResolver(EntityResolver):
    """A resolver that resolves auto approve entity."""

    type_id = "auto_approve"

    def __init__(self) -> None:
        """Initialize the resolver."""
        super().__init__("auto_approve")

    @override
    def matches_reference_dict(self, ref_dict: dict) -> bool:
        """Check if the reference dictionary can be resolved by this resolver."""
        return ref_dict == AutoApprove.ref_dict

    @override
    def _reference_entity(self, entity: Any) -> Mapping[str, str]:
        """Return a reference dictionary for the entity."""
        return AutoApprove.ref_dict

    @override
    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity can be serialized to a reference by this resolver."""
        return isinstance(entity, AutoApprove)

    @override
    def _get_entity_proxy(self, ref_dict: dict) -> AutoApproveProxy:
        """Get the entity proxy for the reference dictionary.

        Note: the proxy is returned to ensure the entity is loaded lazily, when needed.
        :param ref_dict: Reference dictionary.
        """
        return AutoApproveProxy(self, ref_dict)
