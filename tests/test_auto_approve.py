#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from oarepo_workflows.requests.generators import AutoApprove, auto_approve_need
import pytest
from invenio_requests.resolvers.registry import ResolverRegistry

from oarepo_workflows.resolvers.auto_approve import AutoApproveProxy, AutoApproveEntity
from invenio_access.permissions import system_identity


def test_auto_approve_generator():
    a = AutoApprove()

    with pytest.raises(ValueError):
        a.needs()

    with pytest.raises(ValueError):
        a.excludes()

    with pytest.raises(ValueError):
        a.query_filter()

    assert a.reference_receivers() == [{"auto_approve": "True"}]


def test_auto_approve_resolver(app):
    resolved = ResolverRegistry.resolve_entity({"auto_approve": "True"})
    assert isinstance(resolved, AutoApproveEntity)
    #
    # assert resolved.resolve() == AutoApprove()
    # assert resolved.pick_resolved_fields(system_identity, {"id": "true"}) == {"auto_approve": "true"}
    # assert resolved.get_needs() == []

    entity_reference = ResolverRegistry.reference_entity(AutoApproveEntity())
    assert entity_reference == {"auto_approve": "True"}
