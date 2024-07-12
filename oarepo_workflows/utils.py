from itertools import chain
from oarepo_workflows.proxies import current_oarepo_workflows


def get_workflow_from_record(record, **kwargs):
    if hasattr(record, "parent"):
        record = record.parent
    if hasattr(record, "workflow") and record.workflow:
        return record.workflow
    else:
        return None

def needs_from_generators(generators, **kwargs):
    needs = [
        g.needs(
            **kwargs,
        )
        for g in generators
    ]
    return set(chain.from_iterable(needs))

def get_from_requests_workflow(workflow_id, type_id, segment):
    try:
        request = getattr(current_oarepo_workflows.record_workflows[workflow_id].requests, type_id)
        ret = getattr(request, segment)
        return ret
    except (KeyError, AttributeError):
        return []