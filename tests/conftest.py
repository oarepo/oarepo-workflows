#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import json
import sys
import time
from typing import TYPE_CHECKING, Any, cast, override

import pytest
from flask_principal import Need, UserNeed
from invenio_accounts.models import User
from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_permissions.generators import AuthenticatedUser, Generator
from invenio_requests.customizations.event_types import CommentEventType
from invenio_requests.customizations.request_types import RequestType
from invenio_requests.services.permissions import (
    PermissionPolicy as InvenioRequestsPermissionPolicy,
)
from oarepo_model.customizations import AddFileToModule
from oarepo_runtime.services.records.mapping import update_all_records_mappings
from pytest_oarepo.permission_generators import Administration, UserGenerator

from oarepo_workflows import WorkflowRequestPolicy, WorkflowTransitions
from oarepo_workflows.base import Workflow
from oarepo_workflows.model.presets import workflows_preset
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests import WorkflowRequest
from oarepo_workflows.requests.events import WorkflowEvent
from oarepo_workflows.requests.generators import RecipientGeneratorMixin
from oarepo_workflows.services.permissions import DefaultWorkflowPermissions, IfInState

if TYPE_CHECKING:
    from collections.abc import Collection


pytest_plugins = [
    "pytest_oarepo.fixtures",
    "pytest_oarepo.users",
    "pytest_oarepo.roles",
]


@pytest.fixture(scope="module")
def request_types():
    return [
        type("Req", (RequestType,), {"type_id": "req"})(),
        type("Req1", (RequestType,), {"type_id": "req1"})(),
        type("Req2", (RequestType,), {"type_id": "req2"})(),
        type("Req3", (RequestType,), {"type_id": "req3"})(),
    ]


class UserExcluded(Generator):
    """Allows record owners."""

    @override
    def __init__(self, user_email: str) -> None:
        self.user_email = user_email

    @property
    def _user_id(self) -> int:
        # id is Integer column
        return cast("int", User.query.filter_by(email=self.user_email).one().id)

    @override
    def excludes(self, **kwargs: Any) -> Collection[Need]:
        return [UserNeed(self._user_id)]


class TestEventType(CommentEventType):
    """Custom EventType."""

    type_id = "T"


# ---


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


class MyWorkflowRequests(WorkflowRequestPolicy):
    """Requests for testing."""

    req = WorkflowRequest(
        requesters=[IfInState("published", [RecordOwners()])],
        recipients=[Administration()],
        transitions=WorkflowTransitions(
            submitted="considered_for_deletion",
            accepted="deleted",
            declined="published",
        ),
    )


class IsApplicableTestRequestPolicy(WorkflowRequestPolicy):
    """Requests for testing is_applicable."""

    req = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[NullRecipient(), TestRecipient()],
        transitions=WorkflowTransitions(
            submitted="pending",
            accepted="accepted",
            declined="declined",
        ),
        events={
            TestEventType.type_id: WorkflowEvent(submitters=InvenioRequestsPermissionPolicy.can_create_comment),
        },
    )

    req1 = WorkflowRequest(
        requesters=[],
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


@pytest.fixture(scope="module")
def test_draft_service(app):
    """Service instance."""
    return app.extensions["draft_test"].records_service


@pytest.fixture(scope="module")
def auto_approve_service(app):
    """Service instance."""
    return current_oarepo_workflows.auto_approve_service


@pytest.fixture(scope="module")
def multiple_recipients_service(app):
    """Service instance."""
    return current_oarepo_workflows.multiple_recipients_service


@pytest.fixture
def input_data_with_files_disabled(input_data):
    """Input data with files disabled."""
    data = input_data.copy()
    data["files"]["enabled"] = False
    return data


model_types = {
    "Metadata": {
        "properties": {
            "title": {"type": "fulltext+keyword", "required": True},
        }
    }
}


class TestPermissionPolicy(DefaultWorkflowPermissions):
    """Test permission policy."""

    can_manage_files = (AuthenticatedUser(),)


class RecordOwnersReadTestWorkflowPermissionPolicy(TestPermissionPolicy):
    """Test permission policy."""

    can_read = (RecordOwners(),)


class DifferentReadTestWorkflowPermissionPolicy(TestPermissionPolicy):
    """Test permission policy."""

    can_read = (
        UserGenerator("user1@example.org"),
        UserExcluded("user3@example.org"),
        RecordOwners(),
    )


class DifferentReadTestTwoWorkflowPermissionPolicy(TestPermissionPolicy):
    """Test permission policy."""

    can_read = (
        UserGenerator("user3@example.org"),
        UserExcluded("user4@example.org"),
        RecordOwners(),
    )


WORKFLOWS = [
    Workflow(
        code="individual",
        label=_("Default workflow"),
        permission_policy_cls=TestPermissionPolicy,
        request_policy_cls=MyWorkflowRequests,
    ),
    Workflow(
        code="my_workflow",
        label=_("Default custom workflow"),
        permission_policy_cls=TestPermissionPolicy,
        request_policy_cls=MyWorkflowRequests,
    ),
    Workflow(
        code="record_owners_can_read",
        label=_("Record owners read workflow"),
        permission_policy_cls=RecordOwnersReadTestWorkflowPermissionPolicy,
        request_policy_cls=MyWorkflowRequests,
    ),
    Workflow(
        code="is_applicable_workflow",
        label=_("For testing is_applicable"),
        permission_policy_cls=TestPermissionPolicy,
        request_policy_cls=IsApplicableTestRequestPolicy,
    ),
    Workflow(
        code="different_read_1",
        label=_("For testing permissions from multiple workflows"),
        permission_policy_cls=DifferentReadTestWorkflowPermissionPolicy,
        request_policy_cls=MyWorkflowRequests,
    ),
    Workflow(
        code="different_read_2",
        label=_("For testing permissions from multiple workflows"),
        permission_policy_cls=DifferentReadTestTwoWorkflowPermissionPolicy,
        request_policy_cls=MyWorkflowRequests,
    ),
]


@pytest.fixture
def record_service(workflow_model):
    return workflow_model.proxies.current_service


@pytest.fixture
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test"},
        "files": {
            "enabled": True,
        },
    }


@pytest.fixture(scope="module")
def extra_entry_points():
    return {
        "oarepo_workflows.state_changed_notifiers": [
            "test_getter = tests.entrypoints:state_change_notifier_called_marker",
        ],
    }


@pytest.fixture
def default_workflow_json():
    return {
        "parent": {"workflow": "my_workflow"},
        "files": {"enabled": False},
        "metadata": {"title": "Test"},
    }


@pytest.fixture(scope="session")
def workflow_model():
    from oarepo_model.api import model
    from oarepo_rdm.model.presets import rdm_minimal_preset

    t1 = time.time()

    workflow_model = model(
        name="rdm_test",
        version="1.0.0",
        presets=[
            rdm_minimal_preset,
            workflows_preset,
        ],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[
            AddFileToModule(
                "parent-jsonschema",
                "jsonschemas",
                "parent-v1.0.0.json",
                json.dumps(
                    {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "$id": "local://parent-v1.0.0.json",
                        "type": "object",
                        "properties": {"id": {"type": "string"}},
                    }
                ),
            ),
        ],
    )
    workflow_model.register()

    t2 = time.time()
    print(f"Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)  # noqa T201

    try:
        yield workflow_model
    finally:
        workflow_model.unregister()

    return workflow_model


@pytest.fixture(scope="module")
# def app_config(app_config, empty_model, draft_model, draft_model_with_files):
def app_config(app_config, workflow_model, request_types):
    """Override pytest-invenio app_config fixture.

    Needed to set the fields on the custom fields schema.
    """
    app_config["THEME_FRONTPAGE"] = False

    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = {  # hackk to avoid pool_timeout set in invenio_app_rdm
        "pool_pre_ping": False,
        "pool_recycle": 3600,
    }

    app_config["CELERY_ALWAYS_EAGER"] = True
    app_config["CELERY_TASK_ALWAYS_EAGER"] = True

    app_config["WORKFLOWS"] = WORKFLOWS
    app_config["REST_CSRF_ENABLED"] = False

    app_config["RDM_PERSISTENT_IDENTIFIERS"] = {}

    app_config["RDM_OPTIONAL_DOI_VALIDATOR"] = lambda _draft, _previous_published, **_kwargs: True

    app_config["REQUESTS_REGISTERED_TYPES"] = request_types
    # app_confi
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    from invenio_app.factory import create_api

    return create_api


@pytest.fixture(scope="module")
def search_with_field_mapping(app, search):
    """Search fixture."""
    # Ensure all record mappings are updated
    update_all_records_mappings()
    return search
