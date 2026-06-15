#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Base permission policy that overwrites invenio-requests."""

from __future__ import annotations

from typing import Any

from invenio_communities.communities.records.api import Community
from invenio_records_permissions.generators import AnyUser, SystemProcess
from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.services.generators import Creator, Receiver
from invenio_requests.services.permissions import (
    PermissionPolicy as InvenioRequestsPermissionPolicy,
)

from oarepo_workflows import FromRecordWorkflow
from oarepo_workflows.requests.generators.conditionals import IfEventType
from oarepo_workflows.services.permissions.composite import BooleanPermissionPolicyMixin


class CreatorsFromWorkflowRequestsPermissionPolicy(BooleanPermissionPolicyMixin, InvenioRequestsPermissionPolicy):  # type: ignore[reportIncompatibleMethodOverride]
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
        FromRecordWorkflow(
            action=lambda *, request_type, **kwargs: f"{request_type.type_id}_create"  # noqa: ARG005
        ),
    )

    can_create_comment = (
        SystemProcess(),
        IfEventType(CommentEventType, [Creator(), Receiver()]),
        IfEventType(LogEventType, [Creator(), Receiver()]),
        FromRecordWorkflow(
            action=lambda *, request, event_type=CommentEventType, **kwargs: (  # noqa: ARG005
                f"{request.type.type_id}_{event_type.type_id}_create"
            ),
            record_getter=lambda *, request, **kwargs: request.topic.resolve(),  # noqa: ARG005
        ),
    )

    # any user can search for requests, but non-authenticated will not get a hit
    # this is necessary to not have errors on a secret link page (edit/preview form)
    # where the user is not authenticated and search for available requests is performed
    can_search = (*InvenioRequestsPermissionPolicy.can_search, AnyUser())
