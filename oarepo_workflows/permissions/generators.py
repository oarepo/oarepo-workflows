import operator
from functools import reduce
from itertools import chain

from invenio_records.dictutils import dict_lookup
from invenio_records_permissions.generators import ConditionalGenerator, Generator
from invenio_search.engine import dsl

from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.utils import get_workflow_from_record, get_from_requests_workflow


class WorkflowPermission(Generator):
    def __init__(self, action=None):
        # might not be needed in subclasses
        super().__init__()
        self._action = action


    def _get_permission_class_from_workflow(self, record=None, action_name=None, **kwargs):
        if record:
            workflow_id = get_workflow_from_record(record)
            if not workflow_id:
                workflow_id = current_oarepo_workflows.get_default_workflow(record=record, **kwargs)
        else:
            # TODO: should not we raise an exception here ???
            # record doesn't have to be here - ie. in case of create in community, in such case we need default value for the community
            # alternatively, this could be split into more generators
            # holds for if not from above too
            workflow_id = current_oarepo_workflows.get_default_workflow(**kwargs)

        policy = current_oarepo_workflows.record_workflows[workflow_id].permissions
        return policy(action_name, **kwargs)

    def _get_generators(self, record, **kwargs):
        permission_class = self._get_permission_class_from_workflow(
            record, action_name=self._action, **kwargs
        )
        return getattr(permission_class, self._action, None) or []

    def needs(self, record=None, **kwargs):
        generators = self._get_generators(record, **kwargs)
        # todo ui record is RecordItem, it doesn't have state and owners on parent - either do ui serialization of those or resolve them
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

class CreatorsFromWorkflow(WorkflowPermission):
    """
    generator for accesing request creators
    """
    def _get_generators(self, record, **kwargs):
        request_type = kwargs["request_type"]
        workflow_id = get_workflow_from_record(record)
        return get_from_requests_workflow(workflow_id, request_type.type_id, "requesters")


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


