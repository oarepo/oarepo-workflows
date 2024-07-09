from invenio_access.permissions import system_identity


def test_workflow_read(users, logged_client, search_clear, record_service):
    data = record_service.create(system_identity, {})
    assert data._record.parent.workflow == "my_workflow"
    assert data._record.state == "draft"