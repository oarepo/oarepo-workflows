from thesis.resources.records.config import ThesisResourceConfig


def test_workflow_read(users, logged_client, search_clear):
    # create draft
    user_client1 = logged_client(users[0])
    user_client2 = logged_client(users[1])

    create_response = user_client1.post(ThesisResourceConfig.url_prefix, json={})
    draft_json = create_response.json
    assert create_response.status_code == 201

    # in draft state, owner can read, the other user can't
    owner_response = user_client1.get(
        f"{ThesisResourceConfig.url_prefix}{draft_json['id']}/draft"
    )
    other_response = user_client2.get(
        f"{ ThesisResourceConfig.url_prefix}{draft_json['id']}/draft"
    )

    assert owner_response.status_code == 200
    assert other_response.status_code == 403


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
