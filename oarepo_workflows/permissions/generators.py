from itertools import chain

from invenio_records.dictutils import dict_lookup
from invenio_records_permissions.generators import ConditionalGenerator, Generator

from oarepo_workflows.proxies import current_oarepo_workflows


def needs_from_generators(generators, *args, **kwargs):
    needs = [
        g.needs(
            *args,
            **kwargs,
        )
        for g in generators
    ]
    return set(chain.from_iterable(needs))


def _needs_from_workflow(workflow_id, action, record, **kwargs):
    try:
        generators = dict_lookup(
            current_oarepo_workflows, f"{workflow_id}.permissions.{action}"
        )
    except KeyError:
        return []
    return needs_from_generators(generators, record, **kwargs)


class WorkflowPermission(Generator):
    def __init__(self, action):
        super().__init__()
        self._action = action

    def needs(self, record=None, **kwargs):
        if not record:  # invenio requests service does not have a way to input these
            return []
        workflow_id = getattr(record.parent, "workflow", None)
        if not workflow_id:
            return []
        return _needs_from_workflow(
            workflow_id,
            self._action,
            record,
            **kwargs,
        )


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
