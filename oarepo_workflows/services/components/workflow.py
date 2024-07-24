from invenio_records_resources.services.records.components.base import ServiceComponent


class WorkflowComponent(ServiceComponent):

    def create(self, identity, data=None, record=None, **kwargs):
        workflow_id = data["parent"]["workflow_id"]
        record.parent.workflow = workflow_id
