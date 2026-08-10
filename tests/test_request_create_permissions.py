#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Tests for can_create of CreatorsFromWorkflowRequestsPermissionPolicy."""

from __future__ import annotations

import pytest
from flask_principal import Need
from invenio_requests.customizations.request_types import RequestType
from invenio_requests.services.permissions import (
    PermissionPolicy as InvenioRequestsPermissionPolicy,
)

from oarepo_workflows.requests.generators.conditionals import IfTopicTypeIsCommunity, IfTopicTypeIsRecord
from oarepo_workflows.requests.permissions import CreatorsFromWorkflowRequestsPermissionPolicy
from oarepo_workflows.services.permissions.generators import FromCommunityWorkflow, FromRecordWorkflow

TOPIC_TYPE_CONDITION = CreatorsFromWorkflowRequestsPermissionPolicy.can_create[1]


def request_type(*allowed_topic_ref_types: str) -> RequestType:
    return type(
        "Req",
        (RequestType,),
        {"type_id": "req", "allowed_topic_ref_types": list(allowed_topic_ref_types)},
    )()


def test_record_topic_uses_record_workflow():
    """Requests with a record topic take permissions from the record's workflow."""
    generators = TOPIC_TYPE_CONDITION._generators(None, request_type=request_type("record"))  # NOQA: SLF001

    assert len(generators) == 1
    assert isinstance(generators[0], FromRecordWorkflow)
    assert not isinstance(generators[0], FromCommunityWorkflow)


def test_community_topic_uses_community_workflow():
    """Requests with a community topic take permissions from the community's workflow."""
    rt = request_type("community")

    generators = TOPIC_TYPE_CONDITION._generators(None, request_type=rt)  # NOQA: SLF001
    assert len(generators) == 1
    assert isinstance(generators[0], IfTopicTypeIsCommunity)

    generators = generators[0]._generators(None, request_type=rt)  # NOQA: SLF001
    assert len(generators) == 1
    assert isinstance(generators[0], FromCommunityWorkflow)


@pytest.mark.parametrize("context", [{"request_type": request_type("user")}, {}])
def test_other_topic_falls_back_to_invenio_defaults(context):
    """Requests with a topic unrelated to workflows keep the invenio-requests permissions."""
    generators = TOPIC_TYPE_CONDITION._generators(None, **context)  # NOQA: SLF001
    generators = generators[0]._generators(None, **context)  # NOQA: SLF001

    assert generators is InvenioRequestsPermissionPolicy.can_create


def test_multiple_allowed_topic_types_not_supported():
    """A workflow cannot decide which of several topic types to take the workflow from."""
    generator = IfTopicTypeIsRecord(then_=[], else_=[])

    with pytest.raises(ValueError, match="More allowed topic types than one is not allowed"):
        generator._condition(request_type=request_type("record", "community"))  # NOQA: SLF001


def test_from_community_workflow_needs(users, app):
    """The workflow code in the community custom field decides the needs."""
    generator = FromCommunityWorkflow(action=lambda *, request_type, **kwargs: f"{request_type.type_id}_create")  # noqa: ARG005
    community = {"custom_fields": {"workflow": "community_workflow"}}

    needs = generator.needs(record=community, request_type=request_type("community"))

    user_id = users[0].user.id
    assert needs == {Need(method="id", value=user_id), Need(method="system_role", value="system_process")}


@pytest.mark.parametrize("community", [None, {"custom_fields": {}}, {"custom_fields": {"workflow": "does_not_exist"}}])
def test_from_community_workflow_without_workflow(app, community):
    """No community, no workflow on it or an unknown code grants nothing."""
    generator = FromCommunityWorkflow(action="req_create")

    assert generator._get_workflow(community) is None  # NOQA: SLF001
    assert generator.needs(record=community) == []
