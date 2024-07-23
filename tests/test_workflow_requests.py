import pytest
from invenio_records_permissions.generators import Generator
from oarepo_runtime.services.generators import RecordOwners

from oarepo_workflows.requests import RecipientGeneratorMixin, WorkflowRequest
from thesis.thesis.records.api import ThesisRecord


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
    assert req.reference_receivers(record=rec) == {"user": "1"}


def test_request_policy_access(app):
    request_policy = app.config["WORKFLOWS"]["my_workflow"].requests
    assert request_policy["delete_request"]
    with pytest.raises(KeyError):
        assert request_policy["non_existing_request"]
