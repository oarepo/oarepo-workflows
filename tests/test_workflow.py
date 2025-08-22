#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import copy

import pytest

from oarepo_workflows.errors import InvalidWorkflowError


def test_create_without_workflow(workflow_model, users, logged_client, default_workflow_json, search_clear):
    # create draft
    user_client1 = logged_client(users[0])

    create_response = user_client1.post(workflow_model.RecordResourceConfig.url_prefix, json={})
    assert create_response.status_code == 400
    assert create_response.json["errors"][0]["messages"] == ["Workflow not defined in input."]


def test_workflow_read(workflow_model, users, logged_client, default_workflow_json, location, search_clear):
    # create draft
    record = workflow_model.Record
    draft = workflow_model.Draft
    resource_config = workflow_model.RecordResourceConfig
    user_client1 = logged_client(users[0])
    user_client2 = logged_client(users[1])

    create_response = user_client1.post(resource_config.url_prefix, json=default_workflow_json)
    draft_json = create_response.json
    assert create_response.status_code == 201

    record.index.refresh()
    draft.index.refresh()

    # in draft state, owner can read, the other user can't
    owner_response = user_client1.get(f"{resource_config.url_prefix}/{draft_json['id']}/draft")
    other_response = user_client2.get(f"{resource_config.url_prefix}/{draft_json['id']}/draft")

    assert owner_response.status_code == 200
    assert other_response.status_code == 403

    owner_records = user_client1.get(f"/user{resource_config.url_prefix}")
    assert owner_records.status_code == 200
    assert len(owner_records.json["hits"]["hits"]) == 1

    other_records = user_client2.get(f"/user{resource_config.url_prefix}")
    assert other_records.status_code == 200
    assert len(other_records.json["hits"]["hits"]) == 0


def test_workflow_publish(workflow_model, users, logged_client, default_workflow_json, location, search_clear):
    user_client1 = logged_client(users[0])
    user_client2 = logged_client(users[1])
    resource_config = workflow_model.RecordResourceConfig

    create_response = user_client1.post(resource_config.url_prefix, json=default_workflow_json)
    draft_json = create_response.json
    record_id = draft_json["id"]

    assert draft_json["state_timestamp"] is not None

    published_json = user_client1.post(f"{resource_config.url_prefix}/{record_id}/draft/actions/publish").json

    assert draft_json["state_timestamp"] != published_json["state_timestamp"]
    assert published_json["state"] == "published"

    # in published state, all authenticated users should be able to read, this tests that the preset covers
    # read in all states
    owner_response = user_client1.get(f"{resource_config.url_prefix}/{record_id}")
    other_response = user_client2.get(f"{resource_config.url_prefix}/{record_id}")

    assert owner_response.status_code == 200
    assert other_response.status_code == 200

    assert owner_response.json["state_timestamp"] == published_json["state_timestamp"]
    assert owner_response.json["state"] == published_json["state"]
    assert other_response.json["state_timestamp"] == published_json["state_timestamp"]
    assert other_response.json["state"] == published_json["state"]


def test_query_filter(workflow_model, users, logged_client, default_workflow_json, location, search_clear):
    user_client1 = logged_client(users[0])
    user_client2 = logged_client(users[1])
    record = workflow_model.Record
    draft = workflow_model.Draft
    resource_config = workflow_model.RecordResourceConfig

    switched_workflow_input = copy.deepcopy(default_workflow_json)
    switched_workflow_input["parent"]["workflow"] = "record_owners_can_read"

    record_w1 = user_client1.post(resource_config.url_prefix, json=default_workflow_json)

    record_w2 = user_client1.post(
        resource_config.url_prefix,
        json=switched_workflow_input,
    )

    draft_json = record_w1.json

    user_client1.post(f"{resource_config.url_prefix}/{draft_json['id']}/draft/actions/publish")

    draft_json = record_w2.json
    user_client2.post(f"{resource_config.url_prefix}/{draft_json['id']}/draft/actions/publish")

    record.index.refresh()
    draft.index.refresh()

    search_u1 = user_client1.get(resource_config.url_prefix).json
    search_u2 = user_client2.get(resource_config.url_prefix).json

    assert len(search_u1["hits"]["hits"]) == 2
    assert len(search_u2["hits"]["hits"]) == 1


def test_invalid_workflow_input(workflow_model, users, logged_client, default_workflow_json, location, search_clear):
    user_client1 = logged_client(users[0])
    resource_config = workflow_model.RecordResourceConfig

    switched_workflow_input = copy.deepcopy(default_workflow_json)
    switched_workflow_input["parent"]["workflow"] = "fregrthythj"

    invalid_wf_response = user_client1.post(
        resource_config.url_prefix,
        json=switched_workflow_input,
    )
    assert invalid_wf_response.status_code == 400
    assert invalid_wf_response.json["errors"][0]["messages"] == [
        "Workflow fregrthythj does not exist in the configuration. Used on record dict[{'files': "
        "{'enabled': False}, 'metadata': {'title': 'Test'}, 'parent': "
        "{'workflow': 'fregrthythj'}}]"
    ]
    missing_wf_response = user_client1.post(resource_config.url_prefix, json={})
    assert missing_wf_response.status_code == 400
    assert missing_wf_response.json["errors"][0]["messages"] == ["Workflow not defined in input."]


def test_state_change(
    users,
    record_service,
    state_change_function,
    default_workflow_json,
    location,
    search_clear,
):
    record = record_service.create(identity=users[0].identity, data=default_workflow_json)._record  # noqa SLF001
    state_change_function(users[0].identity, record, "approving", commit=False)
    assert record["state"] == "approving"


def test_set_workflow(
    users,
    logged_client,
    default_workflow_json,
    record_service,
    workflow_change_function,
    location,
    search_clear,
):
    record = record_service.create(users[0].identity, default_workflow_json)._record  # noqa SLF001
    with pytest.raises(InvalidWorkflowError):
        workflow_change_function(users[0].identity, record, "invalid_workflow", commit=False)
    workflow_change_function(users[0].identity, record, "record_owners_can_read", commit=False)
    assert record.parent.workflow == "record_owners_can_read"


def test_state_change_entrypoint_hookup(
    users,
    record_service,
    state_change_function,
    default_workflow_json,
    location,
    search_clear,
):
    record = record_service.create(users[0].identity, default_workflow_json)._record  # noqa SLF001
    state_change_function(users[0].identity, record, "approving", commit=False)
    assert record["state-change-notifier-called"]


def test_set_workflow_entrypoint_hookup(
    users,
    logged_client,
    default_workflow_json,
    record_service,
    workflow_change_function,
    location,
    search_clear,
):
    record = record_service.create(users[0].identity, default_workflow_json)._record  # noqa SLF001
    with pytest.raises(InvalidWorkflowError):
        workflow_change_function(users[0].identity, record, "invalid_workflow", commit=False)
    workflow_change_function(users[0].identity, record, "record_owners_can_read", commit=False)
    assert record.parent["workflow-change-notifier-called"]
