#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from flask_principal import UserNeed
from invenio_requests.resolvers.registry import ResolverRegistry
from pytest_oarepo.permission_generators import UserGenerator

from oarepo_workflows.requests.generators.multiple_entities import (
    MultipleEntitiesGenerator,
)
from oarepo_workflows.resolvers.multiple_entities import (
    MultipleEntitiesEntity,
    MultipleEntitiesProxy,
    MultipleEntitiesResolver,
)
from oarepo_workflows.services.multiple_entities import MultipleEntitiesSchema

if TYPE_CHECKING:
    from flask import Flask

from invenio_access.permissions import system_identity


def _multi_ref(*refs: Any) -> str:
    """Build a JSON string for multiple entity references."""
    return json.dumps(list(refs), separators=(", ", ": "))


def test_multiple_recipients_generator(app, users, search_clear) -> None:
    """Test multiple recipients generator."""
    user1 = users[0]
    user2 = users[1]
    a = MultipleEntitiesGenerator(
        [
            UserGenerator(user1.email),
            UserGenerator(user2.email),
        ]
    )

    assert set(a.needs()) == {
        UserNeed(user1.user.id),
        UserNeed(user2.user.id),
    }

    assert not a.excludes()
    assert a.reference_receivers() == [{"multiple": _multi_ref({"user": str(user1.id)}, {"user": str(user2.id)})}]


def test_multiple_recipients_resolver(app: Flask, users, search_clear) -> None:
    """Test multiple recipients resolver."""
    user1 = users[0]
    user2 = users[1]
    multi_ref = _multi_ref({"user": str(user1.id)}, {"user": str(user2.id)})
    resolved = ResolverRegistry.resolve_entity({"multiple": multi_ref})
    assert isinstance(resolved, MultipleEntitiesEntity)
    assert {x.get_needs()[0] for x in resolved.entities} == {
        UserNeed(user1.user.id),
        UserNeed(user2.user.id),
    }
    entity_reference = ResolverRegistry.reference_entity(resolved)
    assert entity_reference == {"multiple": multi_ref}


def test_multiple_entities_entity_proxy(users, workflow_model, roles, location, search_clear):
    user1 = users[0]
    user2 = users[1]
    uid1 = str(user1.id)
    uid2 = str(user2.id)
    multi_ref = _multi_ref({"user": uid1}, {"user": uid2})

    proxy = MultipleEntitiesProxy(MultipleEntitiesResolver(), {"multiple": multi_ref})
    needs = proxy.get_needs()
    assert set(needs) == {UserNeed(user1.user.id), UserNeed(user2.user.id)}
    entity = proxy.resolve()
    assert isinstance(entity, MultipleEntitiesEntity)
    serialization = MultipleEntitiesSchema().dump(entity)

    resolved = proxy.pick_resolved_fields(system_identity, serialization)

    first = resolved["user"][uid1]
    second = resolved["user"][uid2]

    first.pop("confirmed_at")
    second.pop("confirmed_at")

    assert first == {
        "active": True,
        "blocked_at": None,
        "email": "user1@example.org",
        "id": uid1,
        "is_current_user": False,
        "links": {
            "admin_drafts_html": f"https://127.0.0.1:5000/administration/drafts?q=parent.access.owned_by.user:{uid1}&f=allversions",
            "admin_moderation_html": f"https://127.0.0.1:5000/administration/moderation?q=topic.user:{uid1}",
            "admin_records_html": f"https://127.0.0.1:5000/administration/records?q=parent.access.owned_by.user:{uid1}&f=allversions",
            "avatar": f"https://127.0.0.1:5000/api/users/{uid1}/avatar.svg",
            "records_html": f"https://127.0.0.1:5000/search/records?q=parent.access.owned_by.user:{uid1}",
            "self": f"https://127.0.0.1:5000/api/users/{uid1}",
        },
        "profile": {"affiliations": "CERN", "full_name": ""},
        "username": None,
        "verified_at": None,
    }

    assert second == {
        "active": True,
        "blocked_at": None,
        "email": "user2@example.org",
        "id": uid2,
        "is_current_user": False,
        "links": {
            "admin_drafts_html": f"https://127.0.0.1:5000/administration/drafts?q=parent.access.owned_by.user:{uid2}&f=allversions",
            "admin_moderation_html": f"https://127.0.0.1:5000/administration/moderation?q=topic.user:{uid2}",
            "admin_records_html": f"https://127.0.0.1:5000/administration/records?q=parent.access.owned_by.user:{uid2}&f=allversions",
            "avatar": f"https://127.0.0.1:5000/api/users/{uid2}/avatar.svg",
            "records_html": f"https://127.0.0.1:5000/search/records?q=parent.access.owned_by.user:{uid2}",
            "self": f"https://127.0.0.1:5000/api/users/{uid2}",
        },
        "profile": {"affiliations": "CERN", "full_name": ""},
        "username": "beetlesmasher",
        "verified_at": None,
    }

    # must be in the same test due to db issues causing search to not reindex users
    multi_ref_group = _multi_ref({"user": uid1}, {"group": "it-dep"})
    proxy = MultipleEntitiesProxy(MultipleEntitiesResolver(), {"multiple": multi_ref_group})
    entity = proxy.resolve()
    assert isinstance(entity, MultipleEntitiesEntity)
    serialization = MultipleEntitiesSchema().dump(entity)

    resolved = proxy.pick_resolved_fields(system_identity, serialization)

    first = resolved["user"][uid1]
    second = resolved["group"]["it-dep"]

    first.pop("confirmed_at")

    assert first == {
        "active": True,
        "blocked_at": None,
        "email": "user1@example.org",
        "id": uid1,
        "is_current_user": False,
        "links": {
            "admin_drafts_html": f"https://127.0.0.1:5000/administration/drafts?q=parent.access.owned_by.user:{uid1}&f=allversions",
            "admin_moderation_html": f"https://127.0.0.1:5000/administration/moderation?q=topic.user:{uid1}",
            "admin_records_html": f"https://127.0.0.1:5000/administration/records?q=parent.access.owned_by.user:{uid1}&f=allversions",
            "avatar": f"https://127.0.0.1:5000/api/users/{uid1}/avatar.svg",
            "records_html": f"https://127.0.0.1:5000/search/records?q=parent.access.owned_by.user:{uid1}",
            "self": f"https://127.0.0.1:5000/api/users/{uid1}",
        },
        "profile": {"affiliations": "CERN", "full_name": ""},
        "username": None,
        "verified_at": None,
    }

    assert second == {"id": "it-dep", "name": "it-dep"}


def test_service(multiple_recipients_service, users, search_clear):
    user1 = users[0]
    user2 = users[1]
    user3 = users[2]
    uid1 = str(user1.id)
    uid2 = str(user2.id)
    uid3 = str(user3.id)

    multi_ref_12 = _multi_ref({"user": uid1}, {"user": uid2})
    multi_ref_3 = _multi_ref({"user": uid3})

    read_item = multiple_recipients_service.read(system_identity, multi_ref_12)
    assert {"id": multi_ref_12}.items() <= read_item.data.items()
    assert isinstance(read_item._record, MultipleEntitiesEntity)  # noqa SLF001

    refdicts = [entity._ref_dict for entity in read_item._record.entities]  # noqa SLF001
    assert len(refdicts) == 2
    assert {"user": uid1} in refdicts
    assert {"user": uid2} in refdicts

    read_list = multiple_recipients_service.read_many(system_identity, [multi_ref_12, multi_ref_3])
    expected_list = [
        {"id": multi_ref_12},
        {"id": multi_ref_3},
    ]

    assert sorted(read_list.hits, key=str) == sorted(expected_list, key=str)
