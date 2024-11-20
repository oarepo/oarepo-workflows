#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from types import SimpleNamespace

from oarepo_workflows import FromRecordWorkflow
from oarepo_workflows.errors import MissingWorkflowError
from thesis.records.api import ThesisRecord
import pytest

from flask_principal import Identity, UserNeed


def test_get_workflow_id(users, logged_client, search_clear, record_service):
    thesis = ThesisRecord.create({})
    wp = FromRecordWorkflow("read")
    with pytest.raises(MissingWorkflowError):
        wp._get_workflow_id(record=thesis)

    fake_thesis = SimpleNamespace(parent=SimpleNamespace(workflow=""))
    with pytest.raises(MissingWorkflowError):
        assert wp._get_workflow_id(record=fake_thesis)  # noqa


def test_query_filter(users, logged_client, search_clear, record_service):
    wp = FromRecordWorkflow("read")

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    with pytest.raises(MissingWorkflowError):
        assert wp.query_filter(identity=id1) == {}
