#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask_principal import Identity, UserNeed
from invenio_search.engine import dsl

from oarepo_workflows import FromRecordWorkflow, current_oarepo_workflows
from oarepo_workflows.errors import MissingWorkflowError
from oarepo_workflows.services.permissions.generators import InAnyWorkflow


def test_get_workflow_errors(users, workflow_model, logged_client, record_service, location, search_clear):
    fake_record = SimpleNamespace(parent=SimpleNamespace())
    with pytest.raises(MissingWorkflowError, match=r"Parent record does not have a workflow attribute."):
        assert current_oarepo_workflows.get_workflow(fake_record)
    bad_data = {}
    with pytest.raises(MissingWorkflowError, match=r"Record does not have a parent attribute."):
        assert current_oarepo_workflows.get_workflow(bad_data)
    bad_data = {"parent": {}}
    with pytest.raises(MissingWorkflowError, match=r"Parent record does not have a workflow attribute."):
        assert current_oarepo_workflows.get_workflow(bad_data)


# TODO: is the FromRecordWorkflow query filter actually used somewhere?
# the docstring is incorrect, it's not called from WorkflowRecordPermissionPolicy.query_filters but from query filters
# from query filters of the policies associated with workflows
# (eg. oarepo_workflows.services.permissions.workflow_permissions.DefaultWorkflowPermissions) noqa: ERA001
def test_query_filter_missing(users, logged_client, search_clear, record_service):
    wp = FromRecordWorkflow("read")

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    assert wp.query_filter(identity=id1) == dsl.query.Bool(
        should=[
            dsl.query.Bool(
                must=[dsl.query.Terms(state=["draft"]), dsl.query.Terms(parent__access__owned_by__user=[1])]
            ),
            dsl.query.Terms(state=["published"]),
        ]
    )

def test_in_any_workflow(users, logged_client, record_service, workflow_model, location, search_clear):
    record = record_service.create(users[0].identity, {"parent": {"workflow": "my_workflow"}})
    read_needs = InAnyWorkflow("read").needs(record=record._obj)
    read_excludes = InAnyWorkflow("read").excludes(record=record._obj)
    read_query_filter = InAnyWorkflow("read").query_filter(record=record._obj)
    print()
