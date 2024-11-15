from __future__ import annotations

import dataclasses
from functools import cached_property
from datetime import timedelta
from logging import getLogger
from typing import Dict, List, Optional, Tuple

from flask_principal import Need, Permission, Identity
from invenio_access.permissions import SystemRoleNeed
from invenio_records_permissions.generators import Generator

from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests.events import WorkflowEvent

log = getLogger(__name__)


@dataclasses.dataclass
class WorkflowRequest:
    """
    Workflow request definition. The request is defined by the requesters and recipients.
    The requesters are the generators that define who can submit the request. The recipients
    are the generators that define who can approve the request.
    """

    requesters: List[Generator] | Tuple[Generator]
    """Generators that define who can submit the request."""

    recipients: List[Generator] | Tuple[Generator]
    """Generators that define who can approve the request."""

    events: Dict[str, WorkflowEvent] = dataclasses.field(default_factory=lambda: {})
    """Events that can be submitted with the request."""

    transitions: Optional[WorkflowTransitions] = dataclasses.field(
        default_factory=lambda: WorkflowTransitions()
    )
    """Transitions applied to the state of the topic of the request."""

    escalations: Optional[List[WorkflowRequestEscalation]] = None
    """Escalations applied to the request if not approved/declined in time."""

    @cached_property
    def requester_generator(self) -> Generator:
        """
        Return the requesters as a single requester generator.
        """
        return RequesterGenerator(self.requesters)

    def recipient_entity_reference(self, **context) -> Dict | None:
        """
        Return the reference receiver of the workflow request with the given context.
        Note: invenio supports only one receiver, so the first one is returned at the moment.
        Later on, a composite receiver can be implemented.

        :param context: Context of the request.
        """
        return RecipientEntityReference(self, **context)

    def is_applicable(self, identity: Identity, **context) -> bool:
        """
        Check if the request is applicable for the identity and context (which might include record, community, ...).

        :param identity: Identity of the requester.
        :param context: Context of the request that is passed to the requester generators.
        """
        try:
            p = Permission(*self.requester_generator.needs(**context))
            if not p.needs:
                return False
            p.excludes.update(self.requester_generator.excludes(**context))
            return p.allows(identity)
        except Exception as e:
            log.exception("Error checking request applicability: %s", e)
            return False

    @property
    def allowed_events(self) -> Dict[str, WorkflowEvent]:
        """
        Return the allowed events for the workflow request.
        """
        return current_oarepo_workflows.default_workflow_event_submitters | self.events


@dataclasses.dataclass
class WorkflowTransitions:
    """
    Transitions for a workflow request. If the request is submitted and submitted is filled,
    the record (topic) of the request will be moved to state defined in submitted.
    If the request is approved, the record will be moved to state defined in approved.
    If the request is rejected, the record will be moved to state defined in rejected.
    """

    submitted: Optional[str] = None
    accepted: Optional[str] = None
    declined: Optional[str] = None

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(
                f"Transition {item} not defined in {self.__class__.__name__}"
            )


@dataclasses.dataclass
class WorkflowRequestEscalation:
    """
    If the request is not approved/declined/cancelled in time, it might be passed to another recipient
    (such as a supervisor, administrator, ...). The escalation is defined by the time after which the
    request is escalated and the recipients of the escalation.
    """

    after: timedelta
    recipients: List[Generator] | Tuple[Generator]


class WorkflowRequestPolicy:
    """Base class for workflow request policies. Inherit from this class
    and add properties to define specific requests for a workflow.

    The name of the property is the request_type name and the value must be
    an instance of WorkflowRequest.

    Example:

        class MyWorkflowRequests(WorkflowRequestPolicy):
            delete_request = WorkflowRequest(
                requesters = [
                    IfInState("published", RecordOwner())
                ],
                recipients = [CommunityRole("curator")],
                transitions: WorkflowTransitions(
                    submitted = 'considered_for_deletion',
                    approved = 'deleted',
                    rejected = 'published'
                )
            )
    """

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(
                f"Request type {item} not defined in {self.__class__.__name__}"
            )

    @cached_property
    def items(self) -> list[tuple[str, WorkflowRequest]]:
        ret = []
        parent_attrs = set(dir(WorkflowRequestPolicy))
        for attr in dir(self.__class__):
            if parent_attrs and attr in parent_attrs:
                continue
            if attr.startswith("_"):
                continue
            possible_request = getattr(self, attr, None)
            if isinstance(possible_request, WorkflowRequest):
                ret.append((attr, possible_request))
        return ret

    def applicable_workflow_requests(self, identity, **context) -> list[tuple[str, WorkflowRequest]]:
        """
        Return a list of applicable requests for the identity and context.
        """
        ret = []

        for name, request in self.items:
            if request.is_applicable(identity, **context):
                ret.append((name, request))
        return ret


auto_request_need = SystemRoleNeed("auto_request")
auto_approve_need = SystemRoleNeed("auto_approve")


class AutoRequest(Generator):
    """
    Auto request generator. This generator is used to automatically create a request
    when a record is moved to a specific state.
    """

    def needs(self, **kwargs) -> list[Need]:
        """Enabling Needs."""
        return [auto_request_need]


class RecipientGeneratorMixin:
    """
    Mixin for permission generators that can be used as recipients in WorkflowRequest.
    """

    def reference_receivers(self, record=None, request_type=None, **kwargs) -> List[Dict]:
        """
        Taken the context (will include record amd request type at least),
        return the reference receiver(s) of the request.

        Should return a list of dictionary serialization of the receiver classes.

        Might return empty list or None to indicate that the generator does not
        provide any receivers.
        """
        raise NotImplementedError("Implement reference receiver in your code")


class AutoApprove(RecipientGeneratorMixin, Generator):
    """
    Auto approve generator. If the generator is used within recipients of a request,
    the request will be automatically approved when the request is submitted.
    """

    def reference_receivers(self, record=None, request_type=None, **kwargs) -> list[dict[str, str]]:
        return [{"auto_approve": "true"}]


class RequesterGenerator(Generator):
    def __init__(self, requesters) -> None:
        super().__init__()
        self.requesters = requesters

    def needs(self, **context) -> set[Need]:
        """
        Generate a set of needs that requester needs to have in order to create the request.

        :param context: Context of the request.
        :return: Set of needs.
        """

        return {
            need for generator in self.requesters for need in generator.needs(**context)
        }

    def excludes(self, **context) -> set[Need]:
        """
        Generate a set of needs that requester must not have in order to create the request.

        :param context: Context of the request.
        :return: Set of needs.
        """
        return {
            exclude
            for generator in self.requesters
            for exclude in generator.excludes(**context)
        }

    def query_filters(self, **context) -> list[dict]:
        """
        Generate a list of opensearch query filters to get the listing of matching requests.

        :param context: Context of the request.
        """

        return [
            query_filter
            for generator in self.requesters
            for query_filter in generator.query_filter(**context)
        ]


def RecipientEntityReference(
    request: WorkflowRequest, **context
) -> Dict | None:
    """
    Return the reference receiver of the workflow request with the given context.
    Note: invenio supports only one receiver, so the first one is returned at the moment.
    Later on, a composite receiver can be implemented.

    :param request: Workflow request.
    :param context: Context of the request.

    :return: Reference receiver as a dictionary or None if no receiver has been resolved.

    Implementation note: intentionally looks like a class, later on might be converted into one extending from dict.
    """

    if not request.recipients:
        return None

    all_receivers = []
    for generator in request.recipients:
        if isinstance(generator, RecipientGeneratorMixin):
            ref: list[dict] = generator.reference_receivers(**context)
            if ref:
                all_receivers.extend(ref)

    if all_receivers:
        if len(all_receivers) > 1:
            log.debug("Multiple receivers for request %s: %s", request, all_receivers)
        return all_receivers[0]

    return None
