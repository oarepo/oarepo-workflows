from oarepo_workflows.permissions.generators import IfInState
from oarepo_workflows.permissions.policy import WorkflowPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)

from thesis.records.api import ThesisDraft

"""
WORKFLOWS={
  'workflow-name': {
    'label': _('Workflow label'),
    'permissions': WorkflowNamePermissions,
    'requests': WorkflowNameRequests,
  }
}
"""


class DefaultWorkflowPermissions(WorkflowPermissionPolicy):
    can_search = [SystemProcess(), AuthenticatedUser()]
    can_read = [IfInState("draft", [SystemProcess, AuthenticatedUser()]), IfInState("published", [SystemProcess, AnyUser()])]
    can_create = [SystemProcess(), AuthenticatedUser()]
    can_update = [SystemProcess(), AuthenticatedUser()]
    can_delete = [SystemProcess(), AuthenticatedUser()]
    can_manage = [SystemProcess(), AuthenticatedUser()]

import os
import pytest
import yaml
from flask_security import login_user
from invenio_access.permissions import system_identity
from invenio_accounts.testutils import login_user_via_session

from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess
from oarepo_runtime.services.generators import RecordOwners


@pytest.fixture(scope="function")
def sample_metadata_list():
    data_path = f"tests/thesis/data/sample_data.yaml"
    docs = list(yaml.load_all(open(data_path), Loader=yaml.SafeLoader))
    return docs


@pytest.fixture()
def record_service():
    return current_service


@pytest.fixture()
def input_data(sample_metadata_list):
    return sample_metadata_list[0]


def receiver_adressed(*args, **kwargs):
    data = args[4]
    target_community = data["payload"]["community"]
    return {"community": target_community}


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
def logged_client(client):
    def _logged_client(user):
        return LoggedClient(client, user)

    return _logged_client


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


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





    return app_config




@pytest.fixture()
def user(UserFixture, app, db):
    u = UserFixture(
        email="flower@flow.org",
        password="community_flower",
    )
    u.create(app, db)
    return u


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location

from invenio_requests.customizations import RequestType
from invenio_requests.proxies import current_requests


@pytest.fixture(scope="module")
def requests_service(app):
    """Request Factory fixture."""

    return current_requests.requests_service




from thesis.proxies import current_service


@pytest.fixture(scope="function")
def sample_draft(app, db, input_data, community):
    input_data["community_id"] = community.id
    draft_item = current_service.create(system_identity, input_data)
    ThesisDraft.index.refresh()
    return ThesisDraft.pid.resolve(draft_item.id, registered_only=False)















