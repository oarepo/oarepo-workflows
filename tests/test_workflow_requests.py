#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from types import SimpleNamespace

from invenio_records_permissions.generators import Generator
from oarepo_runtime.services.generators import RecordOwners

from oarepo_workflows import WorkflowRequestPolicy
from oarepo_workflows.requests import RecipientGeneratorMixin, WorkflowRequest
from thesis.thesis.records.api import ThesisRecord

from flask_principal import Identity, UserNeed, RoleNeed
from oarepo_runtime.services.permissions.generators import UserWithRole


class TestRecipient(RecipientGeneratorMixin, Generator):
    def reference_receivers(self, record=None, request_type=None, **kwargs):
        assert record is not None
        return [{"user": "1"}]


class NullRecipient(RecipientGeneratorMixin, Generator):
    def reference_receivers(self, record=None, request_type=None, **kwargs):
        return None


def test_workflow_requests(users, logged_client, search_clear, record_service):
    req = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
    )
    rec = ThesisRecord.create({})
    assert req.recipient_entity_reference(record=rec) == {"user": "1"}


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
    class R(WorkflowRequestPolicy):
        req = WorkflowRequest(
            requesters=[RecordOwners()],
            recipients=[NullRecipient(), TestRecipient()],
        )
        req1 = WorkflowRequest(
            requesters=[
                UserWithRole("administrator"),
            ],
            recipients=[NullRecipient(), TestRecipient()],
        )

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
