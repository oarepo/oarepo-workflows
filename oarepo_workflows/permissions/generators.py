import operator
from functools import reduce
from itertools import chain

from invenio_records.dictutils import dict_lookup
from invenio_records_permissions.generators import ConditionalGenerator, Generator
from invenio_search.engine import dsl

from oarepo_workflows.proxies import current_oarepo_workflows


def needs_from_generators(generators, **kwargs):
    if not generators:
        return []
    needs = [
        g.needs(
            **kwargs,
        )
        for g in generators
    ]
    return set(chain.from_iterable(needs))


def reference_receiver_from_generators(generators, **kwargs):
    if not generators:
        return None
    for generator in generators:
        if hasattr(generator, 'reference_receiver'):
            ref = generator.reference_receiver(**kwargs)
            if ref:
                return ref


def query_filters_from_generators(generators, **kwargs):
    queries = [g.query_filter(**kwargs) for g in generators]
    queries = [q for q in queries if q]
    return reduce(operator.or_, queries) if queries else None


def _needs_from_workflow(workflow_id, action, record, **kwargs):
    try:
        generators = dict_lookup(
            current_oarepo_workflows, f"{workflow_id}.permissions.{action}"
        )
    except KeyError:
        return []
    return needs_from_generators(generators, record, **kwargs)


def get_workflow_from_record(record, **kwargs):
    if hasattr(record, "parent"):
        record = record.parent
    if hasattr(record, "workflow") and record.workflow:
        return record.workflow
    else:
        if "record" not in kwargs:
            return current_oarepo_workflows.get_default_workflow(
                record=record, **kwargs
            )
        else:
            return current_oarepo_workflows.get_default_workflow(**kwargs)


def get_permission_class_from_workflow(record=None, action_name=None, **kwargs):
    if record:
        workflow_id = get_workflow_from_record(record)
    else:
        workflow_id = current_oarepo_workflows.get_default_workflow(**kwargs)

    policy = dict_lookup(
        current_oarepo_workflows.record_workflows, f"{workflow_id}.permissions"
    )
    return policy(action_name, **kwargs)


class WorkflowPermission(Generator):
    def __init__(self, action):
        super().__init__()
        self._action = action

    def _get_generators(self, record, **kwargs):
        permission_class = get_permission_class_from_workflow(
            record, action_name=self._action, **kwargs
        )
        return getattr(permission_class, self._action, None)

    def needs(self, record=None, **kwargs):
        generators = self._get_generators(record, **kwargs)
        return needs_from_generators(generators, record=record, **kwargs)

    def query_filter(self, record=None, **kwargs):
        generators = self._get_generators(record, **kwargs)
        return query_filters_from_generators(generators, record=record, **kwargs)


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
