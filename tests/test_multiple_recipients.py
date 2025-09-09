#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

from collections import Counter
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, override
from unittest import result

from flask_principal import Identity, RoleNeed, UserNeed
from invenio_requests.resolvers.registry import ResolverRegistry

# from oarepo_runtime.services.permissions.generators import UserWithRole noqa ERA001
# as OriginalUserWithRole TODO: scrapped in runtime
from opensearch_dsl.query import MatchAll

from oarepo_workflows.requests.generators.multiple_entities import (
    MultipleEntitiesGenerator,
)
from oarepo_workflows.requests.generators.recipient_generator import (
    RecipientGeneratorMixin,
)
from oarepo_workflows.resolvers.multiple_entities import MultipleEntitiesEntity, MultipleEntitiesResolver, \
    MultipleEntitiesProxy
from invenio_users_resources.entity_resolvers import UserProxy, UserResolver
if TYPE_CHECKING:
    from flask import Flask
    from invenio_records_resources.records.api import Record
    from invenio_requests.customizations.request_types import RequestType

# TODO: temp
from invenio_records_permissions.generators import Generator
from invenio_access.permissions import system_identity


class UserGenerator(RecipientGeneratorMixin, Generator):
    def __init__(self, user: str):
        self.user = user

    def needs(self, **kwargs: Any):
        return [UserNeed(self.user)]

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[dict]:
        """Generate a list of reference receivers."""
        # return [{"role": role} for role in self.roles]
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

    #test_identity = Identity(id=1)
    #test_identity.provides.add(RoleNeed("admin"))

    #assert a.query_filter(identity=test_identity) == MatchAll()

    assert a.reference_receivers() == [{"multiple": '[{"user": "1"}, {"user": "2"}]'}]


def test_multiple_recipients_resolver(app: Flask, search_clear) -> None:
    """Test multiple recipients resolver."""
    resolved = ResolverRegistry.resolve_entity({"multiple": '[{"group":"admin"},{"group":"blah"}]'})
    assert isinstance(resolved, MultipleEntitiesEntity)
    assert {x.get_needs()[0] for x in resolved.entities} == {
        RoleNeed("admin"),
        RoleNeed("blah"),
    }

    """
    proxy = MultipleEntitiesProxy(MultipleEntitiesResolver(), {"auto_approve": "true"})

    def test_auto_approve_resolver(app, search_clear):
        resolved = ResolverRegistry.resolve_entity({"auto_approve": "true"})
        assert isinstance(resolved, AutoApprove)



        assert isinstance(proxy.resolve(), AutoApprove)
        assert proxy.pick_resolved_fields(system_identity, {"id": "true"}) == {"auto_approve": "true"}
        assert proxy.get_needs() == []

        entity_reference = ResolverRegistry.reference_entity(AutoApprove())
        assert entity_reference == {"auto_approve": "true"}
    """


    entity_reference = ResolverRegistry.reference_entity(resolved)
    assert entity_reference == {"multiple": '[{"group": "admin"}, {"group": "blah"}]'}


def test_service(multiple_recipients_service):
    read_item = multiple_recipients_service.read(system_identity, '[{"user": "1"}, {"user": "2"}]')
    assert {"id": '[{"user": "1"}, {"user": "2"}]', "entities": [{'user': '1'}, {'user': '2'}]}.items() <= read_item.data.items()
    assert isinstance(read_item._record, MultipleEntitiesEntity) # noqa SLF001

    refdicts = [entity._ref_dict for entity in read_item._record.entities] # noqa SLF001
    assert len(refdicts) == 2
    assert {"user": "1"} in refdicts
    assert {"user": "2"} in refdicts

    read_list = multiple_recipients_service.read_many(system_identity, ['[{"user": "1"}, {"user": "2"}]', '[{"user": "3"}]'])
    expected_list = [{'entities': [{'user': '1'}, {'user': '2'}], 'id': '[{"user": "1"}, {"user": "2"}]'}, {'entities': [{'user': '3'}], 'id': '[{"user": "3"}]'}]

    assert sorted(list(read_list.hits), key=lambda x: str(x)) == sorted(expected_list, key=lambda x: str(x))



