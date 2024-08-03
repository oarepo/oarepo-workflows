from invenio_records_resources.services.records.components.base import ServiceComponent

from oarepo_workflows.errors import MissingWorkflowError
from oarepo_workflows.proxies import current_oarepo_workflows


class WorkflowComponent(ServiceComponent):

    def create(self, identity, data=None, record=None, **kwargs):
        try:
            workflow_id = data["parent"]["workflow"]
        except KeyError:
            raise MissingWorkflowError("Workflow not defined in input.")
        current_oarepo_workflows.set_workflow(
            identity, record, workflow_id, uow=self.uow, **kwargs
        )
