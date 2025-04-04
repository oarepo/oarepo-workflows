#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import os

import pytest
import yaml
from flask_principal import ActionNeed
from flask_security import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api
from invenio_i18n import lazy_gettext as _
from invenio_records_permissions.generators import Generator
from invenio_users_resources.records import UserAggregate
from invenio_requests.customizations.request_types import RequestType
from invenio_requests.proxies import current_request_type_registry
from oarepo_runtime.services.permissions import RecordOwners

from oarepo_workflows.base import Workflow
from oarepo_workflows.requests import (
    WorkflowRequest,
    WorkflowRequestPolicy,
    WorkflowTransitions,
)
from oarepo_workflows.services.permissions import DefaultWorkflowPermissions, IfInState


class RecordOwnersReadTestWorkflowPermissionPolicy(DefaultWorkflowPermissions):
    can_read = [RecordOwners()]


class Administration(Generator):
    def needs(self, **kwargs):
        """Enabling Needs."""
        return [ActionNeed("administration")]

    def query_filter(self, **kwargs):
        """Search filters."""
        from invenio_search.engine import dsl

        return dsl.Q("match_all")


class MyWorkflowRequests(WorkflowRequestPolicy):
    delete_request = WorkflowRequest(
        requesters=[IfInState("published", RecordOwners())],
        recipients=[Administration()],
        transitions=WorkflowTransitions(
            submitted="considered_for_deletion",
            accepted="deleted",
            declined="published",
        ),
    )


class IsApplicableTestRequestPolicy(WorkflowRequestPolicy):
    req = WorkflowRequest(requesters=[RecordOwners()], recipients=[])


WORKFLOWS = {
    "my_workflow": Workflow(
        label=_("Default workflow"),
        permission_policy_cls=DefaultWorkflowPermissions,
        request_policy_cls=MyWorkflowRequests,
    ),
    "record_owners_can_read": Workflow(
        label=_("Record owners read workflow"),
        permission_policy_cls=RecordOwnersReadTestWorkflowPermissionPolicy,
        request_policy_cls=MyWorkflowRequests,
    ),
    "is_applicable_workflow": Workflow(
        label=_("For testing is_applicable"),
        permission_policy_cls=DefaultWorkflowPermissions,
        request_policy_cls=IsApplicableTestRequestPolicy,
    ),
}


@pytest.fixture
def mappings():
    # update the mappings
    from oarepo_runtime.services.custom_fields.mappings import prepare_cf_indices

    from thesis.records.api import ThesisDraft, ThesisRecord

    prepare_cf_indices()
    ThesisDraft.index.refresh()
    ThesisRecord.index.refresh()


@pytest.fixture
def record_service(mappings):
    from thesis.proxies import current_service

    return current_service


@pytest.fixture
def state_change_function():
    from oarepo_workflows.proxies import current_oarepo_workflows

    return current_oarepo_workflows.set_state


@pytest.fixture
def workflow_change_function():
    from oarepo_workflows.proxies import current_oarepo_workflows

    return current_oarepo_workflows.set_workflow


@pytest.fixture(scope="module")
def extra_entry_points():
    return {
        "oarepo_workflows.state_changed_notifiers": [
            "test_getter = tests.utils:test_state_change_notifier",
        ],
        "oarepo_workflows.workflow_changed_notifiers": [
            "test_getter = tests.utils:test_workflow_change_notifier",
        ],
    }


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="function")
def sample_metadata_list():
    data_path = f"tests/thesis/data/sample_data.yaml"
    docs = list(yaml.load_all(open(data_path), Loader=yaml.SafeLoader))
    return docs


@pytest.fixture()
def input_data(sample_metadata_list):
    return sample_metadata_list[0]


@pytest.fixture()
def users(app, db, UserFixture):
    user1 = UserFixture(
        email="user1@example.org",
        password="password",
        active=True,
        confirmed=True,
    )
    user1.create(app, db)

    user2 = UserFixture(
        email="user2@example.org",
        password="beetlesmasher",
        active=True,
        confirmed=True,
    )
    user2.create(app, db)
    db.session.commit()
    UserAggregate.index.refresh()
    return [user1, user2]


class LoggedClient:
    def __init__(self, client, user_fixture):
        self.client = client
        self.user_fixture = user_fixture

    def _login(self):
        login_user(self.user_fixture.user, remember=True)
        login_user_via_session(self.client, email=self.user_fixture.email)

    def post(self, *args, **kwargs):
        self._login()
        return self.client.post(*args, **kwargs)

    def get(self, *args, **kwargs):
        self._login()
        return self.client.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        self._login()
        return self.client.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._login()
        return self.client.delete(*args, **kwargs)


@pytest.fixture()
def logged_client(client, mappings):
    def _logged_client(user):
        return LoggedClient(client, user)

    return _logged_client


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config["RECORDS_REFRESOLVER_CLS"] = (
        "invenio_records.resolver.InvenioRefResolver"
    )
    app_config["RECORDS_REFRESOLVER_STORE"] = (
        "invenio_jsonschemas.proxies.current_refresolver_store"
    )
    app_config["RATELIMIT_AUTHENTICATED_USER"] = "200 per second"
    app_config["SEARCH_HOSTS"] = [
        {
            "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
            "port": os.environ.get("OPENSEARCH_PORT", "9200"),
        }
    ]
    # disable redis cache
    app_config["CACHE_TYPE"] = "SimpleCache"  # Flask-Caching related configs
    app_config["CACHE_DEFAULT_TIMEOUT"] = 300

    app_config["WORKFLOWS"] = WORKFLOWS

    return app_config


@pytest.fixture()
def default_workflow_json():
    return {"parent": {"workflow": "my_workflow"}}


@pytest.fixture()
def extra_request_types():
    def create_rt(type_id):
        return type("Req", (RequestType,), {"type_id": type_id})

    current_request_type_registry.register_type(create_rt("req"), force=True)
    current_request_type_registry.register_type(create_rt("req1"), force=True)
    current_request_type_registry.register_type(create_rt("req2"), force=True)
    current_request_type_registry.register_type(create_rt("req3"), force=True)
