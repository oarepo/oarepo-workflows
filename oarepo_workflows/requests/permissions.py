#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Base permission policy that overwrites invenio-requests."""

from __future__ import annotations

from invenio_records_permissions.generators import SystemProcess
from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.services.generators import Creator, Receiver
from invenio_requests.services.permissions import (
    PermissionPolicy as InvenioRequestsPermissionPolicy,
)

from oarepo_workflows.requests.generators.conditionals import IfEventType
from oarepo_workflows.requests.generators.workflow_based import (
    EventCreatorsFromWorkflow,
    RequestCreatorsFromWorkflow,
)


class CreatorsFromWorkflowRequestsPermissionPolicy(InvenioRequestsPermissionPolicy):
    """Permissions for requests based on workflows.

    This permission adds a special generator RequestCreatorsFromWorkflow() to the default permissions.
    This generator takes a topic, gets the workflow from the topic and returns the generator for
    creators defined on the WorkflowRequest.
    """

    can_create = [
        SystemProcess(),
        RequestCreatorsFromWorkflow(),
    ]

    can_create_comment = [
        SystemProcess(),
        IfEventType(
            [LogEventType.type_id, CommentEventType.type_id], [Creator(), Receiver()]
        ),
        EventCreatorsFromWorkflow(),
    ]
