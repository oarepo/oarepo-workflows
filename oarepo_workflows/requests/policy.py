import dataclasses
import inspect
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from invenio_access.permissions import SystemRoleNeed
from invenio_records_permissions.generators import Generator

from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests.events import WorkflowEvent


@dataclasses.dataclass
class WorkflowRequest:
    requesters: List[Generator] | Tuple[Generator]
    recipients: List[Generator] | Tuple[Generator]
    events: Dict[str, WorkflowEvent] = dataclasses.field(default_factory=lambda: {})
    transitions: Optional["WorkflowTransitions"] = dataclasses.field(
        default_factory=lambda: WorkflowTransitions()
    )
    escalations: Optional[List["WorkflowRequestEscalation"]] = None

    def reference_receivers(self, **kwargs):
        if not self.recipients:
            return None
        for generator in self.recipients:
            if isinstance(generator, RecipientGeneratorMixin):
                ref = generator.reference_receivers(**kwargs)
                if ref:
                    return ref[0]
        return None

    def needs(self, **kwargs):
        return {
            need for generator in self.requesters for need in generator.needs(**kwargs)
        }

    def excludes(self, **kwargs):
        return {
            exclude
            for generator in self.requesters
            for exclude in generator.excludes(**kwargs)
        }

    def query_filters(self, **kwargs):
        return [
            query_filter
            for generator in self.requesters
            for query_filter in generator.query_filter(**kwargs)
        ]

    @property
    def allowed_events(self):
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

    def items(self):
        return inspect.getmembers(self, lambda x: isinstance(x, WorkflowRequest))


class RecipientGeneratorMixin:
    """
    Mixin for permission generators that can be used as recipients in WorkflowRequest.
    """

    def reference_receivers(self, record=None, request_type=None, **kwargs):
        """
        Taken the context (will include record amd request type at least),
        return the reference receiver(s) of the request.

        Should return a list of receiver classes (whatever they are) or dictionary
        serialization of the receiver classes.

        Might return empty list or None to indicate that the generator does not
        provide any receivers.
        """
        raise NotImplementedError("Implement reference receiver in your code")


auto_request_need = SystemRoleNeed("auto_request")
auto_approve_need = SystemRoleNeed("auto_approve")


class AutoRequest(Generator):
    """
    Auto request generator. This generator is used to automatically create a request
    when a record is moved to a specific state.
    """

    def needs(self, **kwargs):
        """Enabling Needs."""
        return [auto_request_need]


class AutoApprove(RecipientGeneratorMixin, Generator):
    """
    Auto approve generator. If the generator is used within recipients of a request,
    the request will be automatically approved when the request is submitted.
    """

    def reference_receivers(self, record=None, request_type=None, **kwargs):
        return [{"auto_approve": "true"}]
