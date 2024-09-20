from functools import cached_property

import importlib_metadata
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_records_resources.services.uow import RecordCommitOp
from oarepo_runtime.datastreams.utils import get_record_service_for_record

from oarepo_workflows.errors import InvalidWorkflowError, MissingWorkflowError
from oarepo_workflows.proxies import current_oarepo_workflows


class OARepoWorkflows(object):

    def __init__(self, app=None):
        if app:
            self.init_config(app)
            self.init_app(app)

    def init_config(self, app):
        """Initialize configuration."""
        from . import ext_config

        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}

        for k in ext_config.OAREPO_PERMISSIONS_PRESETS:
            if k not in app.config["OAREPO_PERMISSIONS_PRESETS"]:
                app.config["OAREPO_PERMISSIONS_PRESETS"][k] = (
                    ext_config.OAREPO_PERMISSIONS_PRESETS[k]
                )

        app.config.setdefault("WORKFLOWS", ext_config.WORKFLOWS)

    @cached_property
    def state_changed_notifiers(self):
        group_name = "oarepo_workflows.state_changed_notifiers"
        return [
            x.load() for x in importlib_metadata.entry_points().select(group=group_name)
        ]

    @cached_property
    def workflow_changed_notifiers(self):
        group_name = "oarepo_workflows.workflow_changed_notifiers"
        return [
            x.load() for x in importlib_metadata.entry_points().select(group=group_name)
        ]

    def set_state(
        self, identity, record, value, *args, uow=None, commit=True, **kwargs
    ):
        previous_value = record.state
        record.state = value
        if commit:
            service = get_record_service_for_record(record)
            uow.register(RecordCommitOp(record, indexer=service.indexer))
        for state_changed_notifier in self.state_changed_notifiers:
            state_changed_notifier(
                identity, record, previous_value, value, *args, uow=uow, **kwargs
            )

    def set_workflow(
        self, identity, record, new_workflow_id, *args, uow=None, commit=True, **kwargs
    ):
        if new_workflow_id not in current_oarepo_workflows.record_workflows:
            raise InvalidWorkflowError(
                f"Workflow {new_workflow_id} does not exist in the configuration."
            )
        previous_value = record.parent.workflow
        record.parent.workflow = new_workflow_id
        if commit:
            service = get_record_service_for_record(record)
            uow.register(
                ParentRecordCommitOp(
                    record.parent, indexer_context=dict(service=service)
                )
            )
        for workflow_changed_notifier in self.workflow_changed_notifiers:
            workflow_changed_notifier(
                identity,
                record,
                previous_value,
                new_workflow_id,
                *args,
                uow=uow,
                **kwargs,
            )

    def get_workflow_from_record(self, record, **kwargs):
        if hasattr(record, "parent"):
            record = record.parent
        if hasattr(record, "workflow") and record.workflow:
            return record.workflow
        else:
            return None

    @property
    def record_workflows(self):
        return self.app.config["WORKFLOWS"]

    @property
    def default_workflow_event_submitters(self):
        if "DEFAULT_WORKFLOW_EVENT_SUBMITTERS" in self.app.config:
            return self.app.config["DEFAULT_WORKFLOW_EVENT_SUBMITTERS"]
        else:
            return {}

    def _get_id_from_record(self, record):
        # community record doesn't have id in dict form, only uuid
        return record["id"] if "id" in record else record.id

    def get_workflow(self, record):
        try:
            return self.record_workflows[record.parent.workflow]
        except AttributeError:
            raise MissingWorkflowError(
                f"Workflow not found on record {self._get_id_from_record(record)}."
            )
        except KeyError:
            raise InvalidWorkflowError(
                f"Workflow {record.parent.workflow} on record {self._get_id_from_record(record)} doesn't exist."
            )

    def init_app(self, app):
        """Flask application initialization."""
        self.app = app
        app.extensions["oarepo-workflows"] = self
