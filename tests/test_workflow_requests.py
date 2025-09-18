#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest
from flask_principal import Identity, UserNeed
from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_requests.proxies import current_requests_service
from opensearch_dsl.query import Terms

from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests import WorkflowRequest
from tests.conftest import NullRecipient, TestRecipient, TestRecipient2


def test_workflow_requests(db, users, workflow_model, logged_client, search_clear, location):
    req = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
    )
    rec = workflow_model.Draft.create({})
    assert req.recipient_entity_reference(record=rec) == {"user": "1"}


def test_workflow_requests_multiple_recipients(db, users, workflow_model, logged_client, search_clear, location):
    req = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[
            TestRecipient(),
            TestRecipient2(),
        ],
    )
    rec = workflow_model.Draft.create({})
    assert req.recipient_entity_reference(record=rec) == {"multiple": '[{"user": "1"}, {"user": "2"}]'}


def test_workflow_requests_no_recipient(workflow_model, users, logged_client, search_clear, location, record_service):
    req1 = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient()],
    )
    rec = workflow_model.Draft.create({})
    assert req1.recipient_entity_reference(record=rec) is None

    req2 = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[],
    )
    assert req2.recipient_entity_reference(record=rec) is None


def test_request_policy_access(app, search_clear):
    requests = current_oarepo_workflows.workflow_by_code["my_workflow"].requests().requests_by_id
    assert len(requests) == 1
    assert "req" in requests


def test_is_applicable(users, logged_client, search_clear, record_service):
    from oarepo_workflows import current_oarepo_workflows

    req = current_oarepo_workflows.workflow_by_code["is_applicable_workflow"].requests().requests_by_id["req"]

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    id2 = Identity(id=2)
    id2.provides.add(UserNeed(2))

    record = SimpleNamespace(
        parent=SimpleNamespace(
            access=(SimpleNamespace(owner=SimpleNamespace(owner_id=1))),
            workflow="is_applicable_workflow",
        )
    )

    assert req.is_applicable(id2, record=record) is False
    assert req.is_applicable(id1, record=record) is True


def test_list_applicable_requests(users, logged_client, search_clear, record_service):
    requests = current_oarepo_workflows.workflow_by_code["is_applicable_workflow"].requests()

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    id2 = Identity(id=2)
    id2.provides.add(UserNeed(2))

    record = SimpleNamespace(
        parent=SimpleNamespace(
            access=(SimpleNamespace(owner=SimpleNamespace(owner_id=1))),
            workflow="is_applicable_workflow",
        )
    )

    assert {x[0] for x in requests.applicable_workflow_requests(id1, record=record)} == {"req"}

    assert {x[0] for x in requests.applicable_workflow_requests(id2, record=record)} == set()


def test_requests_by_id(app, search_clear):
    request_policy = current_oarepo_workflows.workflow_by_code["is_applicable_workflow"].requests()
    assert set(request_policy.requests_by_id.keys()) == {"req", "req1", "req2", "req3"}
    assert list(request_policy.requests_by_id.values()) == request_policy.requests


def test_transition_getter(users, logged_client, search_clear, record_service):
    requests = current_oarepo_workflows.workflow_by_code["is_applicable_workflow"].requests()
    assert requests.requests_by_id["req"].transitions["submitted"] == "pending"
    assert requests.requests_by_id["req"].transitions["accepted"] == "accepted"
    assert requests.requests_by_id["req"].transitions["declined"] == "declined"
    with pytest.raises(KeyError):
        requests.requests_by_id["req"].transitions["non_existing_transition"]


def test_requestor_filter(users, logged_client, search_clear, record_service):
    requests = current_oarepo_workflows.workflow_by_code["is_applicable_workflow"].requests()
    sample_record = SimpleNamespace(
        parent=SimpleNamespace(
            access=(SimpleNamespace(owner=SimpleNamespace(owner_id=1))),
            workflow="is_applicable_workflow",
        )
    )

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    generator = requests.requests_by_id["req"].requester_generator
    assert generator.query_filter(identity=id1, record=sample_record) == Terms(parent__access__owned_by__user=[1])


def test_requests_permissions(workflow_model, users, default_workflow_json, request_types, location, search_clear):
    edited_json = copy.deepcopy(default_workflow_json)  # TODO: leave these to requests? It would be simpler
    edited_json["parent"]["workflow"] = "is_applicable_workflow"
    draft = workflow_model.proxies.current_service.create(users[0].identity, edited_json)
    req_type = next(rt for rt in request_types if rt.type_id == "req")
    with pytest.raises(PermissionDeniedError):
        current_requests_service.create(
            users[1].identity, {}, req_type, None, topic=draft._record, creator=users[1].user
        )
    current_requests_service.create(users[0].identity, {}, req_type, None, topic=draft._record, creator=users[0].user)
