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
from flask_principal import Identity, Need, UserNeed
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


def test_in_any_workflow_query_filter(app, users, search_clear):
    gen = InAnyWorkflow("read")

    user_id = users[2].user.id
    id1 = Identity(id=user_id)
    id1.provides.add(UserNeed(user_id))

    result = gen.query_filter(identity=id1)

    assert isinstance(result, dsl.query.Query)

    result_dict = result.to_dict()
    assert "bool" in result_dict
    assert "should" in result_dict["bool"]

    assert {
        "bool": {
            "must": [
                {"terms": {"parent.access.owned_by.user": [user_id]}},
                {"term": {"parent.workflow": "different_read_1"}},
            ]
        }
    } in result_dict["bool"]["should"]
    assert {
        "bool": {
            "must": [
                {"terms": {"parent.access.owned_by.user": [user_id]}},
                {"term": {"parent.workflow": "different_read_2"}},
            ]
        }
    } in result_dict["bool"]["should"]


def test_in_any_workflow_needs(app, users, search_clear):
    gen = InAnyWorkflow("read")
    result = gen.needs()
    assert Need(method="id", value=users[0].user.id) in result
    assert Need(method="id", value=users[2].user.id) in result


def test_in_any_workflow_excludes(app, users, search_clear):
    """Test that InAnyWorkflow.query_filter OR-combines query_filters from all workflows."""
    gen = InAnyWorkflow("read")
    result = gen.excludes()
    assert Need(method="id", value=users[2].user.id) in result
    assert Need(method="id", value=users[3].user.id) in result


def test_in_any_workflow_allows_with_excludes(
    users, logged_client, record_service, workflow_model, location, search_clear
):
    """Test that InAnyWorkflow allows() evaluates each workflow independently.

    different_read_1: needs={user1}, excludes={user3}
    different_read_2: needs={user3}, excludes={user4}

    With flat union: needs={user1,user3}, excludes={user3,user4} - user3 would be wrongly denied.
    With correct OR semantics: user3 is allowed because different_read_2 independently allows them.
    """
    from invenio_records_permissions import RecordPermissionPolicy

    from oarepo_workflows.services.permissions.record_permission_policy import WorkflowRecordPermissionPolicyMixin

    class _TestPolicy(WorkflowRecordPermissionPolicyMixin, RecordPermissionPolicy):
        can_read = (InAnyWorkflow("read"),)

    policy = _TestPolicy("read")

    # user1 is allowed by different_read_1, not excluded by different_read_2
    assert policy.allows(users[0].identity)

    # user3 is allowed by different_read_2, excluded only by different_read_1
    assert not policy.allows(users[2].identity)

    # user4 is denied: excluded by different_read_2, no matching needs in different_read_1
    assert not policy.allows(users[3].identity)
