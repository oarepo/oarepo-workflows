#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Request workflow policy definition."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from .requests import (
    WorkflowRequest,
)

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.records.api import Record


class WorkflowRequestPolicy:
    """Base class for workflow request policies.

    Inherit from this class
    and add properties to define specific requests for a workflow.

    The name of the property is the request_type name and the value must be
    an instance of WorkflowRequest.

    Example:
        class MyWorkflowRequests(WorkflowRequestPolicy):
            requests = [
                WorkflowRequest(
                    request_type = DeleteRequestType,
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

    @cached_property
    def requests(self) -> list[WorkflowRequest]:
        """Return the list of request types and their instances.

        This call mimics mapping items() method.
        """
        ret = []
        parent_attrs = set(dir(WorkflowRequestPolicy))
        for attr in dir(self.__class__):
            if parent_attrs and attr in parent_attrs:
                continue
            possible_request = getattr(self, attr, None)
            if isinstance(possible_request, WorkflowRequest):
                ret.append(possible_request)
        return ret

    @cached_property
    def requests_by_id(self) -> dict[str, WorkflowRequest]:
        """Return a dictionary of workflow requests by id."""
        return {r.request_type.type_id: r for r in self.requests}

    def __getitem__(self, request_type_id: str) -> WorkflowRequest:
        """Get the workflow request type by its id."""
        return self.requests_by_id[request_type_id]

    def applicable_workflow_requests(
        self, identity: Identity, *, record: Record, **context: Any
    ) -> list[tuple[str, WorkflowRequest]]:
        # TODO: perhaps scrap later if this isn't the best approach to use in requests
        """Return a list of applicable requests for the identity and context.

        :param identity: Identity of the requester.
        :param context: Context of the request that is passed to the requester generators.
        :return: List of tuples (request_type_id, request) that are applicable for the identity and context.
        """
        ret = []

        for name, request in self.requests_by_id.items():
            if request.is_applicable(identity, record=record, **context):
                ret.append((name, request))
        return ret
