from __future__ import annotations

import operator
from functools import reduce
from itertools import chain
from typing import Optional

from flask import Need
from invenio_records_permissions.generators import (ConditionalGenerator,
                                                    Generator)
from invenio_search.engine import dsl

from oarepo_workflows.errors import InvalidWorkflowError, MissingWorkflowError
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests.policy import RecipientGeneratorMixin
from oarepo_workflows.services.permissions.identity import auto_request_need


# invenio_records_permissions.generators.ConditionalGenerator._make_query
def _make_query(generators, **kwargs) -> dict:
    queries = [g.query_filter(**kwargs) for g in generators]
    queries = [q for q in queries if q]
    return reduce(operator.or_, queries) if queries else None


class WorkflowPermission(Generator):
    def __init__(self, action=None) -> None:
        # might not be needed in subclasses
        super().__init__()
        self._action = action

    def _get_workflow_id(self, record=None, **kwargs):
        if record:
            workflow_id = current_oarepo_workflows.get_workflow_from_record(record)
            if not workflow_id:
                raise MissingWorkflowError("Workflow not defined on record.")
        else:
            workflow_id = kwargs.get("data", {}).get("parent", {}).get("workflow", {})
            if not workflow_id:
                raise MissingWorkflowError("Workflow not defined in input.")
        return workflow_id

    def _get_permissions_from_workflow(self, record=None, action_name: Optional[str]=None, **kwargs):
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
    def __init__(self, state, then_) -> None:
        super().__init__(then_, else_=[])
        self.state = state

    def _condition(self, record, **kwargs) -> bool:
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


class SameAs(Generator):
    def __init__(self, as_) -> None:
        self.as_ = as_

    def _generators(self, policy, **kwargs):
        return getattr(policy, self.as_)

    def needs(self, policy, **kwargs) -> set[Need]:
        needs = [
            generator.needs(**kwargs)
            for generator in self._generators(policy, **kwargs)
        ]
        return set(chain.from_iterable(needs))

    def excludes(self, policy, **kwargs) -> set[Need]:
        """Preventing Needs."""
        excludes = [
            generator.excludes(**kwargs)
            for generator in self._generators(policy, **kwargs)
        ]
        return set(chain.from_iterable(excludes))

    def query_filter(self, policy, **kwargs) -> dict:
        """Search filters."""
        return _make_query(self._generators(policy, **kwargs), **kwargs)


class AutoRequest(Generator):
    """
    Auto request generator. This generator is used to automatically create a request
    when a record is moved to a specific state.
    """

    def needs(self, **kwargs) -> list[Need]:
        """Enabling Needs."""
        return [auto_request_need]


class AutoApprove(RecipientGeneratorMixin, Generator):
    """
    Auto approve generator. If the generator is used within recipients of a request,
    the request will be automatically approved when the request is submitted.
    """

    def reference_receivers(self, record=None, request_type=None, **kwargs) -> list[dict[str, str]]:
        return [{"auto_approve": "true"}]
