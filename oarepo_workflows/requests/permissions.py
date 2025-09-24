#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Base permission policy that overwrites invenio-requests."""

from __future__ import annotations

from invenio_records_permissions.generators import AnyUser, SystemProcess
from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.services.generators import Creator, Receiver
from invenio_requests.services.permissions import (
    PermissionPolicy as InvenioRequestsPermissionPolicy,
)

from oarepo_workflows import FromRecordWorkflow
from oarepo_workflows.requests.generators.conditionals import IfEventType


class CreatorsFromWorkflowRequestsPermissionPolicy(InvenioRequestsPermissionPolicy):
    """Permissions for requests based on workflows.

    This permission adds a special generator RequestCreatorsFromWorkflow() to the default permissions.
    This generator takes a topic, gets the workflow from the topic and returns the generator for
    creators defined on the WorkflowRequest.
    """

    can_create = (
        SystemProcess(),
        FromRecordWorkflow(action=lambda *, request_type, **kwargs: f"{request_type.type_id}_create"),  # noqa ARG005
    )

    can_create_comment = (
        SystemProcess(),
        IfEventType(CommentEventType, [Creator(), Receiver()]),
        IfEventType(LogEventType, [Creator(), Receiver()]),
        FromRecordWorkflow(
            action=lambda *, request, event_type, **kwargs: f"{request.type.type_id}_{event_type.type_id}_create",  # noqa ARG005
            record_getter=lambda *, request, **kwargs: request.topic.resolve(),  # noqa ARG005
        ),
    )

    # any user can search for requests, but non-authenticated will not get a hit
    # this is necessary to not have errors on a secret link page (edit/preview form)
    # where the user is not authenticated and search for available requests is performed
    can_search = (*InvenioRequestsPermissionPolicy.can_search, AnyUser())
