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

from flask_principal import Identity, Permission

from oarepo_workflows.proxies import current_oarepo_workflows
from oarepo_workflows.requests import RecipientGeneratorMixin
from oarepo_workflows.requests.generators import MultipleGeneratorsGenerator

if TYPE_CHECKING:
    from datetime import timedelta

    from invenio_records_permissions.generators import Generator

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

    @cached_property
    def requester_generator(self) -> Generator:
        """Return the requesters as a single requester generator."""
        return MultipleGeneratorsGenerator(self.requesters)

    def recipient_entity_reference(self, **context: Any) -> dict | None:
        """Return the reference receiver of the workflow request with the given context.

        Note: invenio supports only one receiver, so the first one is returned at the moment.
        Later on, a composite receiver can be implemented.

        :param context: Context of the request.
        """
        return RecipientEntityReference(self, **context)

    def is_applicable(self, identity: Identity, **context: Any) -> bool:
        """Check if the request is applicable for the identity and context (which might include record, community, ...).

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

    def __getitem__(self, transition_name: str):
        """Get the transition by name."""
        try:
            return getattr(self, transition_name)
        except AttributeError:
            raise KeyError(
                f"Transition {transition_name} not defined in {self.__class__.__name__}"
            ) from None


@dataclasses.dataclass
class WorkflowRequestEscalation:
    """Escalation of the request.

    If the request is not approved/declined/cancelled in time, it might be passed to another recipient
    (such as a supervisor, administrator, ...). The escalation is defined by the time after which the
    request is escalated and the recipients of the escalation.
    """

    after: timedelta
    recipients: list[Generator] | tuple[Generator]


def RecipientEntityReference(request: WorkflowRequest, **context: Any) -> dict | None:
    """Return the reference receiver of the workflow request with the given context.

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