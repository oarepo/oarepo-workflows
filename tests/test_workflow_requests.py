#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from types import SimpleNamespace

import pytest
from flask_principal import Identity, RoleNeed, UserNeed
from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_permissions.generators import Generator
from opensearch_dsl.query import Terms

from oarepo_workflows import WorkflowRequestPolicy, WorkflowTransitions
from oarepo_workflows.requests import WorkflowRequest
from oarepo_workflows.requests.generators import RecipientGeneratorMixin
from tests.test_multiple_recipients import UserWithRole


class TestRecipient(RecipientGeneratorMixin, Generator):
    def reference_receivers(self, record=None, request_type=None, **kwargs):
        assert record is not None
        return [{"user": "1"}]


class TestRecipient2(RecipientGeneratorMixin, Generator):
    def reference_receivers(self, record=None, request_type=None, **kwargs):
        assert record is not None
        return [{"user": "2"}]


class NullRecipient(RecipientGeneratorMixin, Generator):
    def reference_receivers(self, record=None, request_type=None, **kwargs):
        return None


class FailingGenerator(Generator):
    def needs(self, **context):
        raise ValueError("Failing generator")

    def excludes(self, **context):
        raise ValueError("Failing generator")

    def query_filter(self, **context):
        raise ValueError("Failing generator")


class R(WorkflowRequestPolicy):
    req = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
        transitions=WorkflowTransitions(
            submitted="pending",
            accepted="accepted",
            declined="declined",
        ),
    )
    req1 = WorkflowRequest(
        requesters=[
            UserWithRole("administrator"),
        ],
        recipients=[NullRecipient(), TestRecipient()],
    )
    req2 = WorkflowRequest(
        requesters=[],  # never applicable, must be created by, for example, system identity
        recipients=[],
    )
    req3 = WorkflowRequest(
        requesters=[FailingGenerator()],
        recipients=[NullRecipient(), TestRecipient()],
    )


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
    request_policy = app.config["WORKFLOWS"]["my_workflow"].requests()
    assert getattr(request_policy, "delete_request", None)
    assert not getattr(request_policy, "non_existing_request", None)


def test_is_applicable(users, logged_client, search_clear, record_service, extra_request_types):
    req = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
    )
    req._request_type = "req"

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
    requests = R()

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    id2 = Identity(id=2)
    id2.provides.add(UserNeed(2))
    id2.provides.add(RoleNeed("administrator"))

    record = SimpleNamespace(
        parent=SimpleNamespace(
            access=(SimpleNamespace(owner=SimpleNamespace(owner_id=1))),
            workflow="is_applicable_workflow",
        )
    )

    assert set(x[0] for x in requests.applicable_workflow_requests(id1, record=record)) == {"req"}

    assert set(x[0] for x in requests.applicable_workflow_requests(id2, record=record)) == set()


def test_get_workflow_request_via_index(users, logged_client, search_clear, record_service, extra_request_types):
    requests = R()
    assert requests["req"] == requests.req
    assert requests["req1"] == requests.req1
    with pytest.raises(KeyError):
        requests["non_existing_request"]


def test_get_request_type(users, logged_client, search_clear, record_service, extra_request_types):
    requests = R()
    for rt_code, wr in requests.items():
        assert wr.request_type.type_id == rt_code


def test_transition_getter(users, logged_client, search_clear, record_service, extra_request_types):
    requests = R()
    assert requests.req.transitions["submitted"] == "pending"
    assert requests.req.transitions["accepted"] == "accepted"
    assert requests.req.transitions["declined"] == "declined"
    with pytest.raises(KeyError):
        requests.req.transitions["non_existing_transition"]


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

    generator = requests.req.requester_generator
    assert generator.query_filter(identity=id1, record=sample_record) == [Terms(parent__access__owned_by__user=[1])]
