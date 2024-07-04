from invenio_db import db
from invenio_records.systemfields.base import SystemField
from sqlalchemy.exc import NoResultFound

from ...proxies import current_oarepo_workflows


class WorkflowField(SystemField):

    def __init__(self, record_workflow_model, key="workflow"):
        self._workflow = None  # added in db
        self._record_workflow_model = record_workflow_model
        super().__init__(key=key)

    def _get_workflow_from_parent_db(self, record):
        if record.id is None:
            return
        try:
            res = (
                db.session.query(self._record_workflow_model.workflow)
                .filter(self._record_workflow_model.record_id == record.id)
                .one()
            )
            return res[0]
        except NoResultFound:
            return None

    def _get_workflow(self, record):
        if "workflow" in record and record["workflow"]:
            return record["workflow"]
        workflow = self._get_workflow_from_parent_db(record)
        if not workflow:
            workflow = current_oarepo_workflows.get_default_workflow(record=record)
        return workflow

    def post_create(self, record):
        workflow = self._get_workflow(record)
        if workflow:
            self.set_dictkey(record, workflow)

    def pre_commit(self, record):
        super().pre_commit(record)
        saved_workflow = self._get_workflow_from_parent_db(record)
        if not saved_workflow:
            default = self._get_workflow(
                record
            )
            if default:
                new = self._record_workflow_model(
                    workflow=default, record_id=str(record.id)
                )
                db.session.add(new)

    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self
        return self._get_workflow(record)

    def __set__(self, record, value):
        self.set_dictkey(record, value)
