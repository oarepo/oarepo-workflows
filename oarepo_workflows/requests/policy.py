import dataclasses
from typing import List, Optional, Tuple

from invenio_access.permissions import SystemRoleNeed
from invenio_records_permissions.generators import Generator


@dataclasses.dataclass
class WorkflowRequest:
    requesters: List[Generator] | Tuple[Generator]
    recipients: List[Generator] | Tuple[Generator]
    transitions: Optional["WorkflowTransitions"] = dataclasses.field(
        default_factory=lambda: WorkflowTransitions()
    )

    def reference_receivers(self, **kwargs):
        if not self.recipients:
            return None
        for generator in self.recipients:
            if isinstance(generator, RecipientGeneratorMixin):
                ref = generator.reference_receivers(**kwargs)
                if ref:
                    return ref[0]
        return None


@dataclasses.dataclass
class WorkflowTransitions:
    """
    Transitions for a workflow request. If the request is submitted and submitted is filled,
    the record (topic) of the request will be moved to state defined in submitted.
    If the request is approved, the record will be moved to state defined in approved.
    If the request is rejected, the record will be moved to state defined in rejected.
    """

    submitted: Optional[str] = None
    approved: Optional[str] = None
    rejected: Optional[str] = None


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
