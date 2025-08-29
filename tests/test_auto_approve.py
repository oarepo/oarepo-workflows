#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

import pytest
from invenio_access.permissions import system_identity
from invenio_requests.resolvers.registry import ResolverRegistry

from oarepo_workflows.requests import AutoApprove as AutoApproveGenerator
from oarepo_workflows.resolvers.auto_approve import (
    AutoApprove,
    AutoApproveProxy,
    AutoApproveResolver,
)


def test_auto_approve_generator(app, search_clear):
    a = AutoApproveGenerator()

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
    assert isinstance(read_item._obj, AutoApprove)  # noqa SLF001
    assert isinstance(read_item._record, AutoApprove)  # noqa SLF001


def test_auto_approve_resolver(app, search_clear):
    resolved = ResolverRegistry.resolve_entity({"auto_approve": "true"})
    assert isinstance(resolved, AutoApprove)

    proxy = AutoApproveProxy(AutoApproveResolver(), {"auto_approve": "true"})

    assert isinstance(proxy.resolve(), AutoApprove)
    assert proxy.pick_resolved_fields(system_identity, {"id": "true"}) == {"auto_approve": "true"}
    assert proxy.get_needs() == []

    entity_reference = ResolverRegistry.reference_entity(AutoApprove())
    assert entity_reference == {"auto_approve": "true"}
