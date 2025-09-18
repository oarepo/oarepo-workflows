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
from typing import TYPE_CHECKING, Any, cast

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
    from collections.abc import Mapping, Sequence
    from datetime import timedelta

    from flask_principal import Identity
    from invenio_records_permissions.generators import Generator as InvenioGenerator
    from invenio_records_resources.records.api import Record
    from invenio_requests.customizations.request_types import RequestType
    from oarepo_runtime.services.generators import Generator

    from oarepo_workflows.requests.events import WorkflowEvent

log = getLogger(__name__)


@dataclasses.dataclass(kw_only=True)
class WorkflowRequest:
    """Workflow request definition.

    The request is defined by the requesters and recipients.
    The requesters are the generators that define who can submit the request. The recipients
    are the generators that define who can approve the request.
    """

    requesters: Sequence[InvenioGenerator]
    """Generators that define who can submit the request."""

    recipients: Sequence[InvenioGenerator]
    """Generators that define who can approve the request."""

    events: dict[str, WorkflowEvent] = dataclasses.field(default_factory=dict)
    """Events that can be submitted with the request."""

    transitions: WorkflowTransitions | None = dataclasses.field(default_factory=lambda: WorkflowTransitions())
    """Transitions applied to the state of the topic of the request."""

    escalations: list[WorkflowRequestEscalation] | None = None
    """Escalations applied to the request if not approved/declined in time."""

    @cached_property
    def requester_generator(self) -> Generator:
        """Return the requesters as a single requester generator."""
        return MultipleEntitiesGenerator(self.requesters)

    def recipient_entity_reference(self, **context: Any) -> Mapping[str, str] | None:
        """Return the reference receiver of the workflow request with the given context.

        :param context: Context of the request.
        """
        return _get_recipient_entity_reference(self, **context)

    def is_applicable(self, identity: Identity, *, record: Record, **context: Any) -> bool:
        """Check if the request is applicable for the identity and context (which might include record, community, ...).

        :param identity: Identity of the requester.
        :param context: Context of the request that is passed to the requester generators.
        """
        try:
            if hasattr(self.request_type, "is_applicable_to"):
                # invenio RequestType doesn't have is_applicable_to check
                return self.request_type.is_applicable_to(identity, topic=record, **context)  # type: ignore[no-any-return]
            return cast(
                "bool",
                current_requests_service.check_permission(
                    identity,
                    "create",
                    record=record,
                    request_type=self.request_type,
                    **context,
                ),
            )
        except InvalidConfigurationError:
            raise
        except Exception:
            log.exception("Error checking request applicability")
            return False

    @property
    def allowed_events(self) -> dict[str, WorkflowEvent]:
        """Return the allowed events for the workflow request."""
        return current_oarepo_workflows.default_workflow_events | self.events

    def __get__(self, instance: Any, owner: Any) -> WorkflowRequest:
        """Get the workflow request."""
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        """Set the name of the workflow request to the request type id."""
        self._request_type = name

    @property
    def request_type(self) -> RequestType:
        """Return the request type."""
        return current_request_type_registry.lookup(self._request_type, quiet=False)


@dataclasses.dataclass
class WorkflowTransitions:
    """Transitions for a workflow request.

    If the request is submitted and submitted is filled,
    the record (topic) of the request will be moved to state defined in submitted.
    If the request is approved, the record will be moved to state defined in approved.
    If the request is rejected, the record will be moved to state defined in rejected.
    """

    submitted: str | None = None
    accepted: str | None = None
    declined: str | None = None
    cancelled: str | None = None

    def __getitem__(self, transition_name: str):
        """Get the transition by name."""
        if transition_name not in ["submitted", "accepted", "declined", "cancelled"]:
            raise KeyError(f"Transition {transition_name} not defined in {self.__class__.__name__}")
        return getattr(self, transition_name)


@dataclasses.dataclass
class WorkflowRequestEscalation:
    """Escalation of the request.

    If the request is not approved/declined/cancelled in time, it might be passed to another recipient
    (such as a supervisor, administrator, ...). The escalation is defined by the time after which the
    request is escalated and the recipients of the escalation.
    """

    after: timedelta
    recipients: Sequence[InvenioGenerator]

    def recipient_entity_reference(self, **context: Any) -> Mapping[str, str] | None:
        """Return the reference receiver of the workflow escalation with the given context.

        :param context: Context of the request.
        """
        return _get_recipient_entity_reference(self, **context)

    @property
    def escalation_id(self) -> str:
        """Return the escalation ID."""
        return str(self.after.total_seconds())

    def __repr__(self):
        """Return representation of the WorkflowRequestEscalation."""
        return str(self)

    def __str__(self):
        """Return String representation of WorkflowRequestEscalation containing after time and recipients."""
        return f"{self.after=},{self.recipients=}"


def _get_recipient_entity_reference(
    request_or_escalation: WorkflowRequest | WorkflowRequestEscalation, **context: Any
) -> Mapping[str, str] | None:
    """Return the reference receiver of the workflow request or workflow request escalation with the given context.

    Note: invenio supports only one receiver, so the first one is returned at the moment.
    Later on, a composite receiver can be implemented.

    :param request_or_escalation: Workflow request or WorkflowRequestEscalation.
    :param context: Context of the request.

    :return: Reference receiver as a dictionary or None if no receiver has been resolved.
    """
    if not request_or_escalation.recipients:
        return None

    generator = MultipleEntitiesGenerator(request_or_escalation.recipients)
    receivers = generator.reference_receivers(**context)
    return receivers[0] if receivers else None
