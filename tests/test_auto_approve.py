#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import pytest
from invenio_access.permissions import system_identity
from invenio_requests.resolvers.registry import ResolverRegistry

from oarepo_workflows.requests import AutoApprove
from oarepo_workflows.resolvers.auto_approve import AutoApproveEntity, AutoApproveProxy, AutoApproveResolver
from oarepo_workflows.proxies import current_oarepo_workflows


def test_auto_approve_generator(app, search_clear):
    a = AutoApprove()

    with pytest.raises(
        ValueError,
        match="Auto-approve generator can not create needs and "
        "should be used only in `recipient` section of WorkflowRequest.",
    ):
        a.needs()

    with pytest.raises(
        ValueError,
        match="Auto-approve generator can not create needs and "
        "should be used only in `recipient` section of WorkflowRequest.",
    ):
        a.excludes()

    with pytest.raises(
        ValueError,
        match="Auto-approve generator can not create needs and "
        "should be used only in `recipient` section of WorkflowRequest.",
    ):
        a.query_filter()

    assert a.reference_receivers() == [{"auto_approve": "true"}]

def test_auto_approve_service(auto_approve_service):
    read_item = auto_approve_service.read(system_identity, "true")
    assert {"id": "true", "keyword": "auto_approve"}.items() <= read_item.data.items()
    assert isinstance(read_item._obj, AutoApproveEntity)
    assert isinstance(read_item._record, AutoApproveEntity)

def test_auto_approve_resolver(app, search_clear):
    resolved = ResolverRegistry.resolve_entity({"auto_approve": "true"})
    assert isinstance(resolved, AutoApproveEntity)

    proxy = AutoApproveProxy(AutoApproveResolver(), {"auto_approve": "true"})

    assert isinstance(proxy.resolve(), AutoApproveEntity)
    assert proxy.pick_resolved_fields(system_identity, {"id": "true"}) == {"auto_approve": "true"}
    assert proxy.get_needs() == []

    entity_reference = ResolverRegistry.reference_entity(AutoApproveEntity())
    assert entity_reference == {"auto_approve": "true"}
