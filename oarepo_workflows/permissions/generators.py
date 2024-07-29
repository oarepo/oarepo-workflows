from invenio_records_permissions.generators import ConditionalGenerator, Generator
from invenio_search.engine import dsl

from oarepo_workflows.errors import InvalidWorkflowError, MissingWorkflowError
from oarepo_workflows.proxies import current_oarepo_workflows


class WorkflowPermission(Generator):
    def __init__(self, action=None):
        # might not be needed in subclasses
        super().__init__()
        self._action = action

    def _get_workflow_id(self, record=None, **kwargs):
        if record:
            workflow_id = current_oarepo_workflows.get_workflow_from_record(record)
            if not workflow_id:
                raise MissingWorkflowError("Workflow not defined on record.")
        else:
            workflow_id = (
                kwargs.get("data", {}).get("parent", {}).get("workflow_id", {})
            )
            if not workflow_id:
                raise MissingWorkflowError("Workflow not defined in input.")
        return workflow_id

    def _get_permissions_from_workflow(self, record=None, action_name=None, **kwargs):
        workflow_id = self._get_workflow_id(record, **kwargs)
        if workflow_id not in current_oarepo_workflows.record_workflows:
            raise InvalidWorkflowError(
                f"Workflow {workflow_id} does not exist in the configuration."
            )
        policy = current_oarepo_workflows.record_workflows[workflow_id].permissions
        return policy(action_name, record=record, **kwargs)

    def needs(self, record=None, **kwargs):
        return self._get_permissions_from_workflow(record, self._action, **kwargs).needs

    def query_filter(self, record=None, **kwargs):
        return self._get_permissions_from_workflow(
            record, self._action, **kwargs
        ).query_filters


class IfInState(ConditionalGenerator):
    def __init__(self, state, then_):
        super().__init__(then_, else_=[])
        self.state = state

    def _condition(self, record, **kwargs):
        try:
            state = record.state
        except AttributeError:
            return False
        return state == self.state

    def query_filter(self, **kwargs):
        """Filters for queries."""
        field = "state"

        q_instate = dsl.Q("term", **{field: self.state})
        then_query = self._make_query(self.then_, **kwargs)

        return q_instate & then_query
