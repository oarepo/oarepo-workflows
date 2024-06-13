from thesis.resources.records.config import ThesisResourceConfig


def _create_and_publish(client_with_credentials, input_data):
    """Create a draft and publish it."""
    # Create the draft
    response = client_with_credentials.post(
        ThesisResourceConfig.url_prefix, json=input_data
    )

    assert response.status_code == 201

    recid = response.json["id"]

    response = client_with_credentials.post(
        f"{ ThesisResourceConfig.url_prefix}{recid}/draft/actions/publish"
    )

    assert response.status_code == 202
    return recid

def test_publish_draft(client_with_credentials, input_data, search_clear):
    """
    should test the permissions here once the IfInState generators can be used in permission presets
    """
    recid = _create_and_publish(client_with_credentials, input_data)

    # Check draft does not exists anymore
    response = client_with_credentials.get(
        f"{ ThesisResourceConfig.url_prefix}{recid}/draft"
    )

    assert response.status_code == 404

    # Check record exists
    response = client_with_credentials.get(f"{ ThesisResourceConfig.url_prefix}{recid}")

    assert response.status_code == 200
