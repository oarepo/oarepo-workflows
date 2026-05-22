#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Tests for ActionNeed resolver and service."""

from __future__ import annotations

from flask_principal import Need
from invenio_access import ActionNeed
from invenio_access.permissions import system_identity
from invenio_requests.resolvers.registry import ResolverRegistry

from oarepo_workflows.resolvers.action import (
    ActionNeedProxy,
    ActionNeedResolver,
)


def _is_action_need(obj: object) -> bool:
    """Return True when *obj* is a Need whose method is 'action'.

    ``ActionNeed`` is a ``functools.partial``, not a class, so it cannot be
    used as the second argument to ``isinstance()``.  The correct check is to
    verify the underlying ``Need`` namedtuple type and the ``method`` field.
    """
    return isinstance(obj, Need) and obj.method == "action"


def test_action_need_resolver(app, search_clear):
    """Test that the ResolverRegistry resolves ``{"action_need": …}`` to an ActionNeed."""
    resolved = ResolverRegistry.resolve_entity({"action_need": "administration"})

    assert _is_action_need(resolved)
    assert resolved.value == "administration"


def test_action_need_resolver_reference_entity(app, search_clear):
    """Test that the ResolverRegistry turns an ActionNeed back into a ref dict."""
    entity_reference = ResolverRegistry.reference_entity(ActionNeed("administration"))
    assert entity_reference == {"action_need": "administration"}


def test_action_need_proxy_resolve(app, search_clear):
    """Test ActionNeedProxy.resolve returns the ActionNeed for the given action."""
    proxy = ActionNeedProxy(ActionNeedResolver(), {"action_need": "administration"})

    resolved = proxy.resolve()
    assert _is_action_need(resolved)
    assert resolved.value == "administration"


def test_action_need_proxy_get_needs(app, search_clear):
    """Test ActionNeedProxy.get_needs returns the ActionNeed itself."""
    proxy = ActionNeedProxy(ActionNeedResolver(), {"action_need": "administration"})

    needs = proxy.get_needs()
    assert needs == [ActionNeed("administration")]


def test_action_need_proxy_pick_resolved_fields(app, search_clear):
    """Test ActionNeedProxy.pick_resolved_fields returns the original reference dict.

    The ActionNeed entity carries no additional resolvable fields beyond what
    is already encoded in the reference dict, so the method echoes it back.
    """
    ref_dict = {"action_need": "administration"}
    proxy = ActionNeedProxy(ActionNeedResolver(), ref_dict)

    # The resolved_dict argument is intentionally different to confirm that the
    # method always returns the reference dict, not the resolved representation.
    result = proxy.pick_resolved_fields(system_identity, {"id": "administration", "type": "action_need"})
    assert result == ref_dict


def test_action_need_resolver_matches(app, search_clear):
    """Test ActionNeedResolver matching helpers."""
    resolver = ActionNeedResolver()

    assert resolver.matches_reference_dict({"action_need": "administration"})
    assert not resolver.matches_reference_dict({"user": "1"})
    assert not resolver.matches_reference_dict({"auto_approve": "true"})

    assert resolver.matches_entity(ActionNeed("administration"))
    assert not resolver.matches_entity("not-a-need")
    assert not resolver.matches_entity(object())


def test_action_need_service_read(action_need_service):
    """Test ActionNeedService.read returns the correct serialized ActionNeed."""
    read_item = action_need_service.read(system_identity, "administration")

    assert {"id": "administration", "type": "action_need"}.items() <= read_item.data.items()
    assert _is_action_need(read_item._record)  # noqa SLF001
    assert read_item._record.value == "administration"  # noqa SLF001


def test_action_need_service_read_many(action_need_service):
    """Test ActionNeedService.read_many returns one item per action name."""
    read_list = action_need_service.read_many(system_identity, ["administration", "curator"])
    expected_list = [
        {"id": "administration", "type": "action_need"},
        {"id": "curator", "type": "action_need"},
    ]
    assert sorted(read_list.hits, key=str) == sorted(expected_list, key=str)


def test_action_need_service_read_many_duplicates(action_need_service):
    """Test ActionNeedService.read_many returns an item per id, including duplicates."""
    read_list = action_need_service.read_many(system_identity, ["administration", "administration"])
    hits = list(read_list.hits)
    assert len(hits) == 2
    assert all(h == {"id": "administration", "type": "action_need"} for h in hits)
