#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from invenio_access.permissions import system_identity


def test_workflow_read(
    users, logged_client, default_workflow_json, record_service, location, search_clear
):
    data = record_service.create(system_identity, default_workflow_json)
    assert data._record.parent.workflow == "my_workflow"
    assert data._record.state == "draft"
