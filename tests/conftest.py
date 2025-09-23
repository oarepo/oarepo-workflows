#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import base64
import json
import os
import sys
import time
from typing import TYPE_CHECKING, Any, override

import pytest
from flask_principal import ActionNeed, Identity, Need, UserNeed
from flask_security import login_user
from invenio_accounts.proxies import current_datastore
from invenio_accounts.testutils import login_user_via_session
from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_permissions.generators import AuthenticatedUser, Generator
from invenio_requests.customizations.request_types import RequestType
from invenio_search.engine import dsl
from invenio_users_resources.proxies import (
    current_groups_service,
    current_users_service,
)
from oarepo_model.customizations import AddFileToModule
from oarepo_model.presets.records_resources import records_resources_preset
from oarepo_runtime.services.records.mapping import update_all_records_mappings
from sqlalchemy.exc import IntegrityError

from oarepo_workflows import WorkflowRequestPolicy, WorkflowTransitions
from oarepo_workflows.base import Workflow
from oarepo_workflows.model.presets import workflows_preset
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests import WorkflowRequest
from oarepo_workflows.requests.generators import RecipientGeneratorMixin
from oarepo_workflows.services.permissions import DefaultWorkflowPermissions, IfInState

if TYPE_CHECKING:
    from collections.abc import Callable

    from invenio_accounts.models import Role, User


@pytest.fixture(scope="module")
def request_types():
    return [
        type("Req", (RequestType,), {"type_id": "req"})(),
        type("Req1", (RequestType,), {"type_id": "req1"})(),
        type("Req2", (RequestType,), {"type_id": "req2"})(),
        type("Req3", (RequestType,), {"type_id": "req3"})(),
    ]


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


class Administration(Generator):
    """Administration permission generator."""

    @override
    def needs(self, **kwargs: Any):
        return [ActionNeed("administration")]

    @override
    def query_filter(self, **kwargs: Any):
        return dsl.Q("match_all")


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


WORKFLOWS = [
    Workflow(
        code="my_workflow",
        label=_("Default workflow"),
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
    from oarepo_model.presets.drafts import drafts_preset
    from oarepo_rdm.model.presets import rdm_preset

    t1 = time.time()

    workflow_model = model(
        name="rdm_test",
        version="1.0.0",
        presets=[
            records_resources_preset,
            drafts_preset,
            rdm_preset,
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
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
    }

    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config["RECORDS_REFRESOLVER_CLS"] = "invenio_records.resolver.InvenioRefResolver"
    app_config["RECORDS_REFRESOLVER_STORE"] = "invenio_jsonschemas.proxies.current_refresolver_store"

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
def identity_simple():
    """Provide simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    from invenio_app.factory import create_api as _create_api

    return _create_api


#
#
#
#
#
# TODO: use pytest-oarepo instead of this
@pytest.fixture
def password():
    """Password fixture."""
    return base64.b64encode(os.urandom(16)).decode("utf-8")


def _create_role(id_, name, description, is_managed, database) -> Role:
    """Create a Role/Group."""
    r = current_datastore.create_role(id=id_, name=name, description=description, is_managed=is_managed)
    current_datastore.commit()

    current_groups_service.indexer.process_bulk_queue()
    current_groups_service.indexer.refresh()

    return r


@pytest.fixture
def role(db):
    """Create a single group."""
    return _create_role(
        id_="it-dep",
        name="it-dep",
        description="IT Department",
        is_managed=False,
        database=db,
    )


def _create_user(user_fixture, app, db) -> None:
    """Create users, reusing it if it already exists."""
    try:
        user_fixture.create(app, db)
    except IntegrityError:
        datastore = app.extensions["security"].datastore
        user_fixture._user = datastore.get_user_by_email(  # noqa: SLF001
            user_fixture.email
        )
        user_fixture._app = app  # noqa: SLF001
        app.logger.info("skipping creation of %s, already existing", user_fixture.email)


@pytest.fixture
def users(app, db, UserFixture, password):  # noqa: N803 # as it is a fixture name
    """Predefined user fixtures."""
    user1 = UserFixture(
        email="user1@example.org",
        password=password,
        active=True,
        confirmed=True,
        user_profile={
            "affiliations": "CERN",
        },
    )
    _create_user(user1, app, db)

    user2 = UserFixture(
        email="user2@example.org",
        password=password,
        username="beetlesmasher",
        active=True,
        confirmed=True,
        user_profile={
            "affiliations": "CERN",
        },
    )
    _create_user(user2, app, db)

    user3 = UserFixture(
        email="user3@example.org",
        password=password,
        username="beetlesmasherXXL",
        user_profile={
            "full_name": "Maxipes Fik",
            "affiliations": "CERN",
        },
        active=True,
        confirmed=True,
    )
    _create_user(user3, app, db)

    user4 = UserFixture(
        email="user4@example.org",
        password=password,
        username="african",
        preferences={
            "timezone": "Africa/Dakar",  # something without daylight saving time; +0.0
        },
        user_profile={
            "affiliations": "CERN",
        },
        active=True,
        confirmed=True,
    )
    _create_user(user4, app, db)

    user5 = UserFixture(
        email="user5@example.org",
        password=password,
        username="mexican",
        preferences={
            "timezone": "America/Mexico_City",  # something without daylight saving time
        },
        user_profile={
            "affiliations": "CERN",
        },
        active=True,
        confirmed=True,
    )
    _create_user(user5, app, db)

    current_users_service.indexer.process_bulk_queue()
    current_users_service.indexer.refresh()

    return [user1, user2, user3, user4, user5]


class LoggedClient:
    """Logged client for testing."""

    def __init__(self, client, user_fixture):
        """Initialize the logged client."""
        self.client = client
        self.user_fixture = user_fixture

    def _login(self) -> None:
        """Perform login."""
        login_user(self.user_fixture.user, remember=True)
        login_user_via_session(self.client, email=self.user_fixture.email)

    def post(self, *args: Any, **kwargs: Any) -> Any:
        """Send a POST request with authentication."""
        self._login()
        return self.client.post(*args, **kwargs)

    def get(self, *args: Any, **kwargs: Any) -> Any:
        """Send a GET request with authentication."""
        self._login()
        return self.client.get(*args, **kwargs)

    def put(self, *args: Any, **kwargs: Any) -> Any:
        """Send a PUT request with authentication."""
        self._login()
        return self.client.put(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> Any:
        """Send a DELETE request with authentication."""
        self._login()
        return self.client.delete(*args, **kwargs)


@pytest.fixture
def logged_client(client) -> Callable[[User], LoggedClient]:
    def _logged_client(user) -> LoggedClient:
        return LoggedClient(client, user)

    return _logged_client


@pytest.fixture(scope="module")
def search_with_field_mapping(app, search):
    """Search fixture."""
    # Ensure all record mappings are updated
    update_all_records_mappings()
    return search
