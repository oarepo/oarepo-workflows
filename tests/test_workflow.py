from flask_security import logout_user

from thesis.resources.records.config import ThesisResourceConfig
from thesis.thesis.records.api import ThesisDraft, ThesisRecord


def test_workflow_read(users, logged_client, search_clear):
    # create draft
    user_client1 = logged_client(users[0])
    user_client2 = logged_client(users[1])

    create_response = user_client1.post(ThesisResourceConfig.url_prefix, json={})
    draft_json = create_response.json
    assert create_response.status_code == 201

    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()

    # in draft state, owner can read, the other user can't
    owner_response = user_client1.get(
        f"{ThesisResourceConfig.url_prefix}{draft_json['id']}/draft"
    )
    other_response = user_client2.get(
        f"{ ThesisResourceConfig.url_prefix}{draft_json['id']}/draft"
    )

    assert owner_response.status_code == 200
    assert other_response.status_code == 403

    owner_records = user_client1.get("/user/thesis/")
    assert owner_records.status_code == 200
    assert len(owner_records.json["hits"]["hits"]) == 1

    other_records = user_client2.get("user/thesis/")
    assert other_records.status_code == 200
    assert len(other_records.json["hits"]["hits"]) == 0


def test_workflow_publish(users, logged_client, search_clear):
    user_client1 = logged_client(users[0])
    user_client2 = logged_client(users[1])

    create_response = user_client1.post(ThesisResourceConfig.url_prefix, json={})
    draft_json = create_response.json
    user_client1.post(
        f"{ThesisResourceConfig.url_prefix}{draft_json['id']}/draft/actions/publish"
    )

    # in published state, all authenticated users should be able to read, this tests that the preset covers
    # read in all states
    owner_response = user_client1.get(
        f"{ ThesisResourceConfig.url_prefix}{draft_json['id']}"
    )
    other_response = user_client2.get(
        f"{ ThesisResourceConfig.url_prefix}{draft_json['id']}"
    )

    assert owner_response.status_code == 200
    assert other_response.status_code == 200


def test_query_filter(users, client, logged_client, search_clear):
    # todo complete; turns out this is a bit more complicated. needs to make muy own test generators
    user_client1 = logged_client(users[0])

    create_response = user_client1.post(ThesisResourceConfig.url_prefix, json={})
    draft_json = create_response.json
    user_client1.post(
        f"{ThesisResourceConfig.url_prefix}{draft_json['id']}/draft/actions/publish"
    )
    ThesisRecord.index.refresh()

    owner_response = user_client1.get(ThesisResourceConfig.url_prefix).json

    logout_user()
    anon_response = client.get(ThesisResourceConfig.url_prefix).json

    print()


def test_state_change(users, record_service, state_change_function, search_clear):
    record = record_service.create(users[0].identity, {})._record
    state_change_function(users[0].identity, record, "approving")
    assert record["state"] == "approving"


def test_state_change_entrypoint_hookup(
    users, record_service, state_change_function, search_clear
):
    record = record_service.create(users[0].identity, {})._record
    state_change_function(users[0].identity, record, "approving")
    assert record["state"] == "approving"
