#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Workflow requests."""

from __future__ import annotations

import dataclasses
from functools import cached_property
from logging import getLogger
from typing import TYPE_CHECKING, Any, Optional

from invenio_requests.proxies import (
    current_request_type_registry,
    current_requests_service,
)

from oarepo_workflows.errors import InvalidConfigurationError
from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests.generators.multiple_entities import (
    MultipleEntitiesGenerator,
)

if TYPE_CHECKING:
    from datetime import timedelta

    from flask_principal import Identity
    from invenio_records_permissions.generators import Generator
    from invenio_records_resources.records.api import Record
    from invenio_requests.customizations.request_types import RequestType

    from oarepo_workflows.requests.events import WorkflowEvent

log = getLogger(__name__)


@dataclasses.dataclass
class WorkflowRequest:
    """Workflow request definition.

    The request is defined by the requesters and recipients.
    The requesters are the generators that define who can submit the request. The recipients
    are the generators that define who can approve the request.
    """

    requesters: list[Generator] | tuple[Generator]
    """Generators that define who can submit the request."""

    recipients: list[Generator] | tuple[Generator]
    """Generators that define who can approve the request."""

    events: dict[str, WorkflowEvent] = dataclasses.field(default_factory=lambda: {})
    """Events that can be submitted with the request."""

    transitions: Optional[WorkflowTransitions] = dataclasses.field(
        default_factory=lambda: WorkflowTransitions()
    )
    """Transitions applied to the state of the topic of the request."""

    escalations: Optional[list[WorkflowRequestEscalation]] = None
    """Escalations applied to the request if not approved/declined in time."""

    _request_type: RequestType | None = dataclasses.field(default=None, init=False)

    @cached_property
    def requester_generator(self) -> Generator:
        """Return the requesters as a single requester generator."""
        return MultipleEntitiesGenerator(self.requesters)

    def recipient_entity_reference(self, **context: Any) -> dict | None:
        """Return the reference receiver of the workflow request with the given context.

        Note: invenio supports only one receiver, so the first one is returned at the moment.
        Later on, a composite receiver can be implemented.

        :param context: Context of the request.
        """
        return RecipientEntityReference(self, **context)

    def is_applicable(
        self, identity: Identity, *, record: Record, **context: Any
    ) -> bool:
        """Check if the request is applicable for the identity and context (which might include record, community, ...).

        :param identity: Identity of the requester.
        :param context: Context of the request that is passed to the requester generators.
        """
        try:
            if hasattr(self.request_type, "is_applicable_to"):
                # the is_applicable_to must contain a permission check, so do not need to do any check here ...
                return self.request_type.is_applicable_to(
                    identity, topic=record, **context
                )
            else:
                return current_requests_service.check_permission(
                    identity,
                    "create",
                    record=record,
                    request_type=self.request_type,
                    **context,
                )
        except InvalidConfigurationError:
            raise
        except Exception as e:
            log.exception("Error checking request applicability: %s", e)
            return False

    @cached_property
    def request_type(self) -> RequestType:
        """Return the request type for the workflow request."""
        if self._request_type is None:
            raise InvalidConfigurationError(
                f"Probably this WorkflowRequest ({self}) is not part of a Workflow. "
                "Please add it to a workflow or manually set the ._request_type attribute "
                "to a code of a registered request type."
            )
        try:
            return current_request_type_registry.lookup(self._request_type)
        except KeyError as e:
            raise InvalidConfigurationError(
                f"Request type {self._request_type} not found in the request type registry."
            ) from e

    @property
    def allowed_events(self) -> dict[str, WorkflowEvent]:
        """Return the allowed events for the workflow request."""
        return current_oarepo_workflows.default_workflow_events | self.events


@dataclasses.dataclass
class WorkflowTransitions:
    """Transitions for a workflow request.

    If the request is submitted and submitted is filled,
    the record (topic) of the request will be moved to state defined in submitted.
    If the request is approved, the record will be moved to state defined in approved.
    If the request is rejected, the record will be moved to state defined in rejected.
    """

    submitted: Optional[str] = None
    accepted: Optional[str] = None
    declined: Optional[str] = None
    cancelled: Optional[str] = None

    def __getitem__(self, transition_name: str):
        """Get the transition by name."""
        if transition_name not in ["submitted", "accepted", "declined", "cancelled"]:
            raise KeyError(
                f"Transition {transition_name} not defined in {self.__class__.__name__}"
            )
        return getattr(self, transition_name)


@dataclasses.dataclass
class WorkflowRequestEscalation:
    """Escalation of the request.

    If the request is not approved/declined/cancelled in time, it might be passed to another recipient
    (such as a supervisor, administrator, ...). The escalation is defined by the time after which the
    request is escalated and the recipients of the escalation.
    """

    after: timedelta
    recipients: list[Generator] | tuple[Generator]

    @property
    def escalation_id(self):
        """Return the escalation ID."""
        return str(self.after.total_seconds())

    def __repr__(self):
        """Representation of the WorkflowRequestEscalation."""
        return str(self)

    def __str__(self):
        """String representation of WorkflowRequestEscalation containing after time and recipients."""
        return f'{self.after=},{self.recipients=}'

# noinspection PyPep8Naming
def RecipientEntityReference(request_or_escalation: WorkflowRequest | WorkflowRequestEscalation,
                             **context: Any) -> dict | None:
    """Return the reference receiver of the workflow request or workflow request escalation with the given context.

    Note: invenio supports only one receiver, so the first one is returned at the moment.
    Later on, a composite receiver can be implemented.

    :param request_or_escalation: Workflow request or WorkflowRequestEscalation.
    :param context: Context of the request.

    :return: Reference receiver as a dictionary or None if no receiver has been resolved.

    Implementation note: intentionally looks like a class, later on might be converted into one extending from dict.
    """
    if not request_or_escalation.recipients:
        return None

    generator = MultipleEntitiesGenerator(request_or_escalation.recipients)
    receivers = generator.reference_receivers(**context)
    return receivers[0] if receivers else None
