#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from types import SimpleNamespace

from invenio_records_permissions.generators import Generator
from oarepo_runtime.services.permissions import RecordOwners, UserWithRole

from oarepo_workflows import WorkflowRequestPolicy, WorkflowTransitions
from oarepo_workflows.requests import RecipientGeneratorMixin, WorkflowRequest
from thesis.thesis.records.api import ThesisRecord

from flask_principal import Identity, UserNeed, RoleNeed
import pytest
from opensearch_dsl.query import Terms


class TestRecipient(RecipientGeneratorMixin, Generator):
    def reference_receivers(self, record=None, request_type=None, **kwargs):
        assert record is not None
        return [{"user": "1"}]


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
        requesters = [],    # never applicable, must be created by, for example, system identity
        recipients = []
    )
    req3 = WorkflowRequest(
        requesters = [FailingGenerator()],
        recipients = [NullRecipient(), TestRecipient()],
    )

def test_workflow_requests(users, logged_client, search_clear, record_service):
    req = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
    )
    rec = ThesisRecord.create({})
    assert req.recipient_entity_reference(record=rec) == {"user": "1"}

def test_workflow_requests_no_recipient(users, logged_client, search_clear, record_service):
    req1 = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient()],
    )
    rec = ThesisRecord.create({})
    assert req1.recipient_entity_reference(record=rec) is None

    req2 = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[],
    )
    assert req2.recipient_entity_reference(record=rec) is None

def test_request_policy_access(app):
    request_policy = app.config["WORKFLOWS"]["my_workflow"].requests()
    assert getattr(request_policy, "delete_request", None)
    assert not getattr(request_policy, "non_existing_request", None)


def test_is_applicable(users, logged_client, search_clear, record_service):
    req = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
    )
    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    id2 = Identity(id=2)
    id2.provides.add(UserNeed(2))

    record = SimpleNamespace(parent=SimpleNamespace(owners=[SimpleNamespace(id=1)]))
    assert req.is_applicable(id2, record=record) is False
    assert req.is_applicable(id1, record=record) is True


def test_list_applicable_requests(users, logged_client, search_clear, record_service):


    requests = R()

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    id2 = Identity(id=2)
    id2.provides.add(UserNeed(2))
    id2.provides.add(RoleNeed("administrator"))

    record = SimpleNamespace(parent=SimpleNamespace(owners=[SimpleNamespace(id=1)]))

    assert set(
        x[0] for x in requests.applicable_workflow_requests(id1, record=record)
    ) == {"req"}

    assert set(
        x[0] for x in requests.applicable_workflow_requests(id2, record=record)
    ) == {"req1"}


def test_get_request_type(users, logged_client, search_clear, record_service):
    requests = R()
    assert requests["req"] == requests.req
    assert requests["req1"] == requests.req1
    with pytest.raises(KeyError):
        requests["non_existing_request"]        # noqa

def test_transition_getter(users, logged_client, search_clear, record_service):
    requests = R()
    assert requests.req.transitions['submitted'] == 'pending'
    assert requests.req.transitions['accepted'] == 'accepted'
    assert requests.req.transitions['declined'] == 'declined'
    with pytest.raises(KeyError):
        requests.req.transitions['non_existing_transition']        # noqa


def test_requestor_filter(users, logged_client, search_clear, record_service):
    requests = R()
    sample_record = SimpleNamespace(parent=SimpleNamespace(owners=[SimpleNamespace(id=1)]))

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    generator = requests.req.requester_generator
    assert generator.query_filter(identity=id1, record=sample_record) == [Terms(parent__owners__user=[1])]