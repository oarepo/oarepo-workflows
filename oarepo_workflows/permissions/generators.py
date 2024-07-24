import operator
from functools import reduce
from itertools import chain

from invenio_records_permissions.generators import ConditionalGenerator, Generator
from invenio_search.engine import dsl

from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.utils import get_workflow_from_record


class WorkflowPermission(Generator):
    def __init__(self, action=None):
        # might not be needed in subclasses
        super().__init__()
        self._action = action

    def _get_workflow_in_permissions(self, record=None, **kwargs):
        workflow_id = None
        if record:
            workflow_id = get_workflow_from_record(record)
        if not workflow_id:
            try:
                workflow_id = kwargs["data"]["parent"]["workflow_id"]
            except KeyError:
                pass
        return workflow_id

    def _get_permission_class_from_workflow(
        self, record=None, action_name=None, **kwargs
    ):
        workflow_id = self._get_workflow_in_permissions(record, **kwargs)
        policy = current_oarepo_workflows.record_workflows[workflow_id].permissions
        return policy(action_name, **kwargs)

    def _get_generators(self, record=None, **kwargs):
        permission_class = self._get_permission_class_from_workflow(
            record, action_name=self._action, **kwargs
        )
        return getattr(permission_class, self._action, None) or []

    def needs(self, record=None, **kwargs):
        generators = self._get_generators(record, **kwargs)
        # todo ui record is RecordItem, it doesn't have state and owners on parent - either do ui serialization of those or resolve them - made a change into oarepo-ui for this
        needs = [
            g.needs(
                record=record,
                **kwargs,
            )
            for g in generators
        ]
        return set(chain.from_iterable(needs))

    def query_filter(self, record=None, **kwargs):
        generators = self._get_generators(record, **kwargs)

        queries = [g.query_filter(record=record, **kwargs) for g in generators]
        queries = [q for q in queries if q]
        return reduce(operator.or_, queries) if queries else None


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

        q_instate = dsl.Q("match", **{field: self.state})
        then_query = self._make_query(self.then_, **kwargs)

        return q_instate & then_query
