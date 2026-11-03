# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Base permission policy that overwrites invenio-requests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_communities.communities.records.api import Community
from invenio_records_permissions.generators import AnyUser, SystemProcess
from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.services.permissions import (
    PermissionPolicy as InvenioRequestsPermissionPolicy,
)

from oarepo_workflows import FromRecordWorkflow
from oarepo_workflows.requests.generators.conditionals import (
    IfEventType,
    IfTopicTypeIsCommunity,
    IfTopicTypeIsRecord,
)
from oarepo_workflows.services.permissions.composite import BooleanPermissionPolicyMixin
from oarepo_workflows.services.permissions.generators import FromCommunityWorkflow

if TYPE_CHECKING:
    from invenio_records_resources.records import Record
    from invenio_requests.customizations import EventType, RequestType
    from invenio_requests.records.api import Request


def _create_action(*, request_type: RequestType, **_: Any) -> str:
    return f"{request_type.type_id}_create"


def _event_create_action(*, request: Request, event_type: type[EventType] = CommentEventType, **_: Any) -> str:
    return f"{request.type.type_id}_{event_type.type_id}_create"


def _request_topic(*, request: Request, **_: Any) -> Record:
    return request.topic.resolve()


class CreatorsFromWorkflowRequestsPermissionPolicy(BooleanPermissionPolicyMixin, InvenioRequestsPermissionPolicy):
    """Permissions for requests based on workflows.

    This permission adds a special generator RequestCreatorsFromWorkflow() to the default permissions.
    This generator takes a topic, gets the workflow from the topic and returns the generator for
    creators defined on the WorkflowRequest.
    """

    def __init__(self, action: str, **kwargs: Any):
        """Create a permission policy for the given action and kwargs."""
        if (
            action == "create"
            and "community" not in kwargs
            and "receiver" in kwargs
            and isinstance(kwargs["receiver"], Community)
        ):
            kwargs["community"] = kwargs["receiver"]
        super().__init__(action=action, **kwargs)

    can_create = (
        SystemProcess(),
        IfTopicTypeIsRecord(
            then_=[
                FromRecordWorkflow(action=_create_action),
            ],
            else_=[
                IfTopicTypeIsCommunity(
                    then_=[FromCommunityWorkflow(action=_create_action)],
                    else_=InvenioRequestsPermissionPolicy.can_create,
                )
            ],
        ),
    )

    can_create_comment = (
        SystemProcess(),
        IfEventType(CommentEventType, InvenioRequestsPermissionPolicy.can_create_comment),
        IfEventType(LogEventType, InvenioRequestsPermissionPolicy.can_create_comment),
        FromRecordWorkflow(
            action=_event_create_action,
            record_getter=_request_topic,
        ),
    )

    # any user can search for requests, but non-authenticated will not get a hit
    # this is necessary to not have errors on a secret link page (edit/preview form)
    # where the user is not authenticated and search for available requests is performed
    can_search = (*InvenioRequestsPermissionPolicy.can_search, AnyUser())
