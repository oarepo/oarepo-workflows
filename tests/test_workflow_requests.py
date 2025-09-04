#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, override

import pytest
from flask_principal import Identity, UserNeed
from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_permissions.generators import Generator
from invenio_requests.customizations.request_types import RequestType
from opensearch_dsl.query import Terms

from oarepo_workflows import WorkflowRequestPolicy, WorkflowTransitions
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests import WorkflowRequest
from oarepo_workflows.requests.generators import RecipientGeneratorMixin
from tests.test_multiple_recipients import UserWithRole


class TestRecipient(RecipientGeneratorMixin, Generator):
    """User recipient for testing purposes."""

    @override
    def reference_receivers(self, record=None, request_type=None, **context: Any):
        assert record is not None
        return [{"user": "1"}]


class TestRecipient2(RecipientGeneratorMixin, Generator):
    """User recipient for testing purposes."""

    @override
    def reference_receivers(self, record=None, request_type=None, **context: Any):
        assert record is not None
        return [{"user": "2"}]


class NullRecipient(RecipientGeneratorMixin, Generator):
    """Null recipient for testing purposes."""

    @override
    def reference_receivers(self, record=None, request_type=None, **context: Any):
        return None


class FailingGenerator(Generator):
    """Failing generator for testing purposes."""

    @override
    def needs(self, **context: Any):
        raise ValueError("Failing generator")

    @override
    def excludes(self, **context: Any):
        raise ValueError("Failing generator")

    @override
    def query_filter(self, **context: Any):
        raise ValueError("Failing generator")


class R(WorkflowRequestPolicy):
    """Requests for testing purposes."""

    requests = [
        WorkflowRequest(
            request_type=type("Req", (RequestType,), {"type_id": "req"}),
            requesters=[RecordOwners()],
            recipients=[NullRecipient(), TestRecipient()],
            transitions=WorkflowTransitions(
                submitted="pending",
                accepted="accepted",
                declined="declined",
            ),
        ),
        WorkflowRequest(
            request_type=type("Req1", (RequestType,), {"type_id": "req1"}),
            requesters=[
                UserWithRole("administrator"),
            ],
            recipients=[NullRecipient(), TestRecipient()],
        ),
        WorkflowRequest(
            request_type=type("Req2", (RequestType,), {"type_id": "req2"}),
            requesters=[],  # never applicable, must be created by, for example, system identity
            recipients=[],
        ),
        WorkflowRequest(
            request_type=type("Req3", (RequestType,), {"type_id": "req3"}),
            requesters=[FailingGenerator()],
            recipients=[NullRecipient(), TestRecipient()],
        ),
    ]


def test_workflow_requests(db, users, workflow_model, logged_client, search_clear, location):
    req = WorkflowRequest(
        request_type=type("Req", (RequestType,), {"type_id": "req"}),
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
    )
    rec = workflow_model.Draft.create({})
    assert req.recipient_entity_reference(record=rec) == {"user": "1"}


def test_workflow_requests_multiple_recipients(db, users, workflow_model, logged_client, search_clear, location):
    req = WorkflowRequest(
        request_type=type("Req", (RequestType,), {"type_id": "req"}),
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
        request_type=type("Req", (RequestType,), {"type_id": "req"}),
        requesters=[RecordOwners()],
        recipients=[NullRecipient()],
    )
    rec = workflow_model.Draft.create({})
    assert req1.recipient_entity_reference(record=rec) is None

    req2 = WorkflowRequest(
        request_type=type("Req", (RequestType,), {"type_id": "req"}),
        requesters=[RecordOwners()],
        recipients=[],
    )
    assert req2.recipient_entity_reference(record=rec) is None


def test_request_policy_access(app, search_clear):
    requests = current_oarepo_workflows.workflow_by_code["my_workflow"].requests().requests_by_id
    assert len(requests) == 1
    assert "req1" in requests


def test_is_applicable(users, logged_client, search_clear, record_service, extra_request_types):
    # THIS IS WRONG AND WORKS ONLY BY ACCIDENT!!!!!
    # TODO: this approach won't work as the "from workflow" needs are taken from the workflow not this req

    req = WorkflowRequest(
        request_type=type("Req", (RequestType,), {"type_id": "req"}),
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
    )

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


def test_list_applicable_requests(users, logged_client, search_clear, record_service, extra_request_types):
    # THIS IS WRONG AND WORKS ONLY BY ACCIDENT!!!!!

    requests = R()

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


def test_requests_by_id():
    requests = R()
    assert set(requests.requests_by_id.keys()) == {"req", "req1", "req2", "req3"}
    assert list(requests.requests_by_id.values()) == R.requests


def test_transition_getter(users, logged_client, search_clear, record_service, extra_request_types):
    requests = R()
    assert requests.requests_by_id["req"].transitions["submitted"] == "pending"
    assert requests.requests_by_id["req"].transitions["accepted"] == "accepted"
    assert requests.requests_by_id["req"].transitions["declined"] == "declined"
    with pytest.raises(KeyError):
        requests.requests_by_id["req"].transitions["non_existing_transition"]


def test_requestor_filter(users, logged_client, search_clear, record_service, extra_request_types):
    requests = R()
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
