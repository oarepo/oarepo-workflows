#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask_principal import Identity, RoleNeed
from invenio_requests.resolvers.registry import ResolverRegistry

# from oarepo_runtime.services.permissions.generators import UserWithRole noqa ERA001
# as OriginalUserWithRole TODO: scrapped in runtime
from opensearch_dsl.query import MatchAll, MatchNone

from oarepo_workflows.requests.generators.multiple_entities import (
    MultipleEntitiesGenerator,
)
from oarepo_workflows.requests.generators.recipient_generator import (
    RecipientGeneratorMixin,
)
from oarepo_workflows.resolvers.multiple_entities import MultipleEntitiesEntity

if TYPE_CHECKING:
    from flask import Flask
    from invenio_records_resources.records.api import Record
    from invenio_requests.customizations.request_types import RequestType

# TODO: temp
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl


class OriginalUserWithRole(Generator):
    """Tempo moved from runtime."""

    def __init__(self, *roles: str):
        """Construct the generator."""
        self.roles = roles

    @override
    def needs(self, **kwargs: Any):
        return [RoleNeed(role) for role in self.roles]

    @override
    def query_filter(self, identity=None, **kwargs: Any):
        if not identity:
            return dsl.Q("match_none")
        for provide in identity.provides:
            if provide.method == "role" and provide.value in self.roles:
                return dsl.Q("match_all")
        return dsl.Q("match_none")


class UserWithRole(RecipientGeneratorMixin, OriginalUserWithRole):
    """User with role generator."""

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[dict]:
        """Generate a list of reference receivers."""
        return [{"role": role} for role in self.roles]


def test_multiple_recipients_generator(app, search_clear) -> None:
    """Test multiple recipients generator."""
    a = MultipleEntitiesGenerator(
        [
            UserWithRole("admin"),
            UserWithRole("blah"),
        ]
    )

    assert set(a.needs()) == {
        RoleNeed("admin"),
        RoleNeed("blah"),
    }

    assert not a.excludes()

    test_identity = Identity(id=1)
    test_identity.provides.add(RoleNeed("admin"))

    assert a.query_filter(identity=test_identity) == [MatchAll(), MatchNone()]

    assert a.reference_receivers() == [{"multiple": '[{"role": "admin"}, {"role": "blah"}]'}]


def test_multiple_recipients_resolver(app: Flask, search_clear) -> None:
    """Test multiple recipients resolver."""
    resolved = ResolverRegistry.resolve_entity({"multiple": '[{"group":"admin"},{"group":"blah"}]'})
    assert isinstance(resolved, MultipleEntitiesEntity)
    assert {x.get_needs()[0] for x in resolved.entities} == {
        RoleNeed("admin"),
        RoleNeed("blah"),
    }

    entity_reference = ResolverRegistry.reference_entity(resolved)
    assert entity_reference == {"multiple": '[{"group": "admin"}, {"group": "blah"}]'}
