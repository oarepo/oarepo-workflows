#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Request workflow policy definition."""

from __future__ import annotations

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

    def __init__(self):
        """Initialize the request policy."""
        for rt_code, rt in self.items():
            rt._request_type = rt_code

    def __getitem__(self, request_type_id: str) -> WorkflowRequest:
        """Get the workflow request type by its id."""
        try:
            return getattr(self, request_type_id)
        except AttributeError:
            raise KeyError(
                f"Request type {request_type_id} not defined in {self.__class__.__name__}"
            ) from None

    def items(self) -> list[tuple[str, WorkflowRequest]]:
        """Return the list of request types and their instances.

        This call mimics mapping items() method.
        """
        ret = []
        parent_attrs = set(dir(WorkflowRequestPolicy))
        for attr in dir(self.__class__):
            if parent_attrs and attr in parent_attrs:
                continue
            if attr.startswith("_"):
                continue
            possible_request = getattr(self, attr, None)
            if isinstance(possible_request, WorkflowRequest):
                ret.append((attr, possible_request))
        return ret

    def applicable_workflow_requests(
        self, identity: Identity, *, record: Record, **context: Any
    ) -> list[tuple[str, WorkflowRequest]]:
        """Return a list of applicable requests for the identity and context.

        :param identity: Identity of the requester.
        :param context: Context of the request that is passed to the requester generators.
        :return: List of tuples (request_type_id, request) that are applicable for the identity and context.
        """
        ret = []

        for name, request in self.items():
            if request.is_applicable(identity, record=record, **context):
                ret.append((name, request))
        return ret
