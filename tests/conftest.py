import os

import pytest
import yaml
from flask_security import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api
from invenio_i18n import lazy_gettext as _
from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess
from invenio_users_resources.records import UserAggregate
from oarepo_runtime.services.generators import RecordOwners

from oarepo_workflows.permissions.generators import IfInState
from oarepo_workflows.permissions.policy import DefaultWorkflowPermissionPolicy

# tests should not depend on specified default configuration


class TestWorkflowPermissionPolicy(DefaultWorkflowPermissionPolicy):
    can_search = [AuthenticatedUser()]
    can_read = [
        IfInState("draft", [RecordOwners()]),
        IfInState("published", [AuthenticatedUser()]),
    ]
    can_update = [IfInState("draft", RecordOwners())]
    can_delete = [
        IfInState("draft", RecordOwners()),
        # published record can not be deleted directly by anyone else than system
        SystemProcess(),
    ]
    can_create = [AuthenticatedUser()]
    can_publish = [AuthenticatedUser()]


WORKFLOWS = {
    "default": {
        "label": _("Default workflow"),
        "permissions": DefaultWorkflowPermissionPolicy,
        "requests": {},
    }
}


@pytest.fixture
def record_service():
    from thesis.proxies import current_service

    return current_service


@pytest.fixture
def state_change_function():
    from oarepo_workflows.proxies import current_oarepo_workflows

    return current_oarepo_workflows.set_state


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
def logged_client(client):
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

    app_config["RECORD_WORKFLOWS"] = WORKFLOWS

    return app_config
