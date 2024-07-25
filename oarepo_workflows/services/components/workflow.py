from invenio_records_resources.services.records.components.base import ServiceComponent

from oarepo_workflows.errors import InvalidWorkflowError, MissingWorkflowError
from oarepo_workflows.proxies import current_oarepo_workflows


class WorkflowComponent(ServiceComponent):

    def create(self, identity, data=None, record=None, **kwargs):
        try:
            workflow_id = data["parent"]["workflow_id"]
        except KeyError:
            raise MissingWorkflowError("Workflow not defined in input.")
        available_workflows = current_oarepo_workflows.record_workflows.keys()
        if workflow_id not in available_workflows:
            raise InvalidWorkflowError(
                f"Workflow {workflow_id} does not exist in the configuration."
            )
        record.parent.workflow = workflow_id
