#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask_principal import UserNeed
from invenio_requests.resolvers.registry import ResolverRegistry

from oarepo_workflows.requests.generators.multiple_entities import (
    MultipleEntitiesGenerator,
)
from oarepo_workflows.requests.generators.recipient_generator import (
    RecipientGeneratorMixin,
)
from oarepo_workflows.resolvers.multiple_entities import (
    MultipleEntitiesEntity,
    MultipleEntitiesProxy,
    MultipleEntitiesResolver,
)
from oarepo_workflows.services.multiple_entities import MultipleEntitiesSchema

if TYPE_CHECKING:
    from flask import Flask
    from invenio_records_resources.records.api import Record
    from invenio_requests.customizations.request_types import RequestType

from invenio_access.permissions import system_identity
from invenio_records_permissions.generators import Generator


class UserGenerator(RecipientGeneratorMixin, Generator):
    """Generator for test purposes."""

    def __init__(self, user: str):
        """Init the generator."""
        self.user = user

    @override
    def needs(self, **kwargs: Any):
        """Return the needs."""
        return [UserNeed(self.user)]

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[dict]:
        """Generate a list of reference receivers."""
        return [{"user": self.user}]


def test_multiple_recipients_generator(app, search_clear) -> None:
    """Test multiple recipients generator."""
    a = MultipleEntitiesGenerator(
        [
            UserGenerator("1"),
            UserGenerator("2"),
        ]
    )

    assert set(a.needs()) == {
        UserNeed("1"),
        UserNeed("2"),
    }

    assert not a.excludes()
    assert a.reference_receivers() == [{"multiple": '[{"user": "1"}, {"user": "2"}]'}]


def test_multiple_recipients_resolver(app: Flask, search_clear) -> None:
    """Test multiple recipients resolver."""
    resolved = ResolverRegistry.resolve_entity({"multiple": '[{"user": "1"}, {"user": "2"}]'})
    assert isinstance(resolved, MultipleEntitiesEntity)
    assert {x.get_needs()[0] for x in resolved.entities} == {
        UserNeed(1),
        UserNeed(2),
    }
    entity_reference = ResolverRegistry.reference_entity(resolved)
    assert entity_reference == {"multiple": '[{"user": "1"}, {"user": "2"}]'}


def test_multiple_entities_entity_proxy(users, role, workflow_model, location, search_clear):
    proxy = MultipleEntitiesProxy(MultipleEntitiesResolver(), {"multiple": '[{"user": "1"}, {"user": "2"}]'})
    needs = proxy.get_needs()
    assert set(needs) == {UserNeed(1), UserNeed(2)}
    entity = proxy.resolve()
    assert isinstance(entity, MultipleEntitiesEntity)
    serialization = MultipleEntitiesSchema().dump(entity)

    resolved = proxy.pick_resolved_fields(system_identity, serialization)

    first = resolved["user"]["1"]
    second = resolved["user"]["2"]

    first.pop("confirmed_at")
    second.pop("confirmed_at")

    assert first == {
        "active": True,
        "blocked_at": None,
        "email": "user1@example.org",
        "id": "1",
        "is_current_user": False,
        "links": {
            "admin_drafts_html": "https://127.0.0.1:5000/administration/drafts?q=parent.access.owned_by.user:1&f=allversions",
            "admin_moderation_html": "https://127.0.0.1:5000/administration/moderation?q=topic.user:1",
            "admin_records_html": "https://127.0.0.1:5000/administration/records?q=parent.access.owned_by.user:1&f=allversions",
            "avatar": "https://127.0.0.1:5000/api/users/1/avatar.svg",
            "records_html": "https://127.0.0.1:5000/search/records?q=parent.access.owned_by.user:1",
            "self": "https://127.0.0.1:5000/api/users/1",
        },
        "profile": {"affiliations": "CERN", "full_name": ""},
        "username": None,
        "verified_at": None,
    }

    assert second == {
        "active": True,
        "blocked_at": None,
        "email": "user2@example.org",
        "id": "2",
        "is_current_user": False,
        "links": {
            "admin_drafts_html": "https://127.0.0.1:5000/administration/drafts?q=parent.access.owned_by.user:2&f=allversions",
            "admin_moderation_html": "https://127.0.0.1:5000/administration/moderation?q=topic.user:2",
            "admin_records_html": "https://127.0.0.1:5000/administration/records?q=parent.access.owned_by.user:2&f=allversions",
            "avatar": "https://127.0.0.1:5000/api/users/2/avatar.svg",
            "records_html": "https://127.0.0.1:5000/search/records?q=parent.access.owned_by.user:2",
            "self": "https://127.0.0.1:5000/api/users/2",
        },
        "profile": {"affiliations": "CERN", "full_name": ""},
        "username": "beetlesmasher",
        "verified_at": None,
    }

    # must be in the same test due to db issues causing search to not reindex users
    proxy = MultipleEntitiesProxy(MultipleEntitiesResolver(), {"multiple": '[{"user": "1"}, {"group": "it-dep"}]'})
    entity = proxy.resolve()
    assert isinstance(entity, MultipleEntitiesEntity)
    serialization = MultipleEntitiesSchema().dump(entity)

    resolved = proxy.pick_resolved_fields(system_identity, serialization)

    first = resolved["user"]["1"]
    second = resolved["group"]["it-dep"]

    first.pop("confirmed_at")

    assert first == {
        "active": True,
        "blocked_at": None,
        "email": "user1@example.org",
        "id": "1",
        "is_current_user": False,
        "links": {
            "admin_drafts_html": "https://127.0.0.1:5000/administration/drafts?q=parent.access.owned_by.user:1&f=allversions",
            "admin_moderation_html": "https://127.0.0.1:5000/administration/moderation?q=topic.user:1",
            "admin_records_html": "https://127.0.0.1:5000/administration/records?q=parent.access.owned_by.user:1&f=allversions",
            "avatar": "https://127.0.0.1:5000/api/users/1/avatar.svg",
            "records_html": "https://127.0.0.1:5000/search/records?q=parent.access.owned_by.user:1",
            "self": "https://127.0.0.1:5000/api/users/1",
        },
        "profile": {"affiliations": "CERN", "full_name": ""},
        "username": None,
        "verified_at": None,
    }

    assert second == {"id": "it-dep", "name": "it-dep"}


def test_service(multiple_recipients_service, users, search_clear):
    read_item = multiple_recipients_service.read(system_identity, '[{"user": "1"}, {"user": "2"}]')
    assert {"id": '[{"user": "1"}, {"user": "2"}]'}.items() <= read_item.data.items()
    assert isinstance(read_item._record, MultipleEntitiesEntity)  # noqa SLF001

    refdicts = [entity._ref_dict for entity in read_item._record.entities]  # noqa SLF001
    assert len(refdicts) == 2
    assert {"user": "1"} in refdicts
    assert {"user": "2"} in refdicts

    read_list = multiple_recipients_service.read_many(
        system_identity, ['[{"user": "1"}, {"user": "2"}]', '[{"user": "3"}]']
    )
    expected_list = [
        {"id": '[{"user": "1"}, {"user": "2"}]'},
        {"id": '[{"user": "3"}]'},
    ]

    assert sorted(read_list.hits, key=lambda x: str(x)) == sorted(expected_list, key=lambda x: str(x))
