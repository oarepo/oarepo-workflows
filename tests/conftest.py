import pytest
from oarepo_model.customizations import AddEntryPoint, AddModule
from oarepo_model.presets.drafts import drafts_presets

from oarepo_workflows.model.presets import workflows_presets


@pytest.fixture(scope="module")
def test_draft_service(app):
    """Service instance."""
    return app.extensions["draft_test"].records_service

"""
@pytest.fixture(scope="module")
def draft_service_with_files(app):
    return app.extensions["draft_with_files"].records_service

@pytest.fixture(scope="module")
def draft_file_service(app):
    return app.extensions["draft_with_files"].draft_files_service



@pytest.fixture(scope="module")
def file_service(app):
    return app.extensions["test"].files_service
"""


@pytest.fixture(scope="function")
def input_data_with_files_disabled(input_data):
    """Input data with files disabled."""
    data = input_data.copy()
    data["files"]["enabled"] = False
    return data


import copy
import json
import sys
import time

import pytest
from flask_principal import Identity, Need, UserNeed
from oarepo_model.presets.records_resources import records_resources_presets

pytest_plugins = ("celery.contrib.pytest", "pytest_oarepo.users", "pytest_oarepo.fixtures")


parent_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "local://parent-v1.0.0.json",
    "type": "object",
    "properties": {"id": {"type": "string"}},
}

model_types = {
    "Metadata": {
        "properties": {
            "title": {"type": "fulltext+keyword", "required": True},
        }
    }
}
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

"""
pytest_plugins = [
    "pytest_oarepo.communities.fixtures",
    "pytest_oarepo.communities.records",
    "pytest_oarepo.requests.fixtures",
    "pytest_oarepo.records",
    ,
    ,
    "pytest_oarepo.files",
    "pytest_oarepo.vocabularies"
]
"""

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
def state_change_function():
    from oarepo_workflows.proxies import current_oarepo_workflows

    return current_oarepo_workflows.set_state


@pytest.fixture
def workflow_change_function():
    from oarepo_workflows.proxies import current_oarepo_workflows

    return current_oarepo_workflows.set_workflow

@pytest.fixture
def record_service(draft_model):
    return draft_model.proxies.current_service

"""
@pytest.fixture(scope="function")
def sample_metadata_list():
    data_path = f"tests/thesis/data/sample_data.yaml"
    docs = list(yaml.load_all(open(data_path), Loader=yaml.SafeLoader))
    return docs



@pytest.fixture()
def input_data(sample_metadata_list):
    return sample_metadata_list[0]
"""

@pytest.fixture(scope="function")
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test"},
        "files": {
            "enabled": True,
        },
    }

import pytest
from importlib_metadata import EntryPoint
from unittest.mock import patch

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

"""
@pytest.fixture
def mappings():
    # update the mappings
    from oarepo_runtime.services.custom_fields.mappings import prepare_cf_indices

    from thesis.records.api import ThesisDraft, ThesisRecord

    prepare_cf_indices()
    ThesisDraft.index.refresh()
    ThesisRecord.index.refresh()
"""


@pytest.fixture()
def default_workflow_json():
    return {"parent": {"workflow": "my_workflow"},
            "files": {"enabled": False},
            "metadata": {"title": "Test"},
            }


@pytest.fixture()
def extra_request_types():
    def create_rt(type_id):
        return type("Req", (RequestType,), {"type_id": type_id})

    current_request_type_registry.register_type(create_rt("req"), force=True)
    current_request_type_registry.register_type(create_rt("req1"), force=True)
    current_request_type_registry.register_type(create_rt("req2"), force=True)
    current_request_type_registry.register_type(create_rt("req3"), force=True)



@pytest.fixture(scope="module")
def draft_model():
    from oarepo_model.api import model
    from oarepo_model.customizations import AddFileToModule
    from oarepo_model.presets.rdm import rdm_presets

    t1 = time.time()

    draft_model = model(
        name="draft_test",
        version="1.0.0",
        presets=[records_resources_presets, drafts_presets, rdm_presets, workflows_presets],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[
            # needs https://github.com/inveniosoftware/invenio-search/pull/238/files
            # add parent JSON schema
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
    draft_model.register()

    t2 = time.time()
    print(f"Draft Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)

    return draft_model

@pytest.fixture(scope="module")
#def app_config(app_config, empty_model, draft_model, draft_model_with_files):
def app_config(app_config, draft_model):
    """Override pytest-invenio app_config fixture.

    Needed to set the fields on the custom fields schema.
    """
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
    }

    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config["RECORDS_REFRESOLVER_CLS"] = (
        "invenio_records.resolver.InvenioRefResolver"
    )
    app_config["RECORDS_REFRESOLVER_STORE"] = (
        "invenio_jsonschemas.proxies.current_refresolver_store"
    )

    app_config["THEME_FRONTPAGE"] = False

    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = (
        {  # hack to avoid pool_timeout set in invenio_app_rdm
            "pool_pre_ping": False,
            "pool_recycle": 3600,
        }
    )

    app_config["CELERY_ALWAYS_EAGER"] = True
    app_config["CELERY_TASK_ALWAYS_EAGER"] = True

    # app_config["SQLALCHEMY_ECHO"] = True

    app_config["WORKFLOWS"] = WORKFLOWS
    app_config["INVENIO_RDM_ENABLED"] = True
    app_config["REST_CSRF_ENABLED"] = False

    return app_config


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
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