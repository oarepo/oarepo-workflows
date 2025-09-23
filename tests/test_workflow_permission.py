#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask_principal import Identity, UserNeed

from oarepo_workflows import FromRecordWorkflow, current_oarepo_workflows
from oarepo_workflows.errors import InvalidWorkflowError, MissingWorkflowError


def test_get_workflow_id(users, workflow_model, logged_client, record_service, location, search_clear):
    record = workflow_model.Draft.create({})
    wp = FromRecordWorkflow("read")
    with pytest.raises(InvalidWorkflowError):
        wp._get_workflow(record=record)  # noqa SLF001

    fake_record = SimpleNamespace(parent=SimpleNamespace(workflow=""))
    with pytest.raises(InvalidWorkflowError):
        assert wp._get_workflow(record=fake_record)  # noqa SLF001


def test_get_workflow_errors(users, workflow_model, logged_client, record_service, location, search_clear):
    fake_record = SimpleNamespace(parent=SimpleNamespace())
    with pytest.raises(MissingWorkflowError, match=r"Parent record does not have a workflow attribute."):
        assert current_oarepo_workflows.get_workflow(fake_record)
    bad_data = {}
    with pytest.raises(MissingWorkflowError, match=r"Record does not have a parent attribute."):
        assert current_oarepo_workflows.get_workflow(bad_data)
    bad_data = {"parent": {}}
    with pytest.raises(MissingWorkflowError, match=r"Parent record does not have a workflow attribute."):
        assert current_oarepo_workflows.get_workflow(bad_data)


def test_query_filter_missing(users, logged_client, search_clear, record_service):
    wp = FromRecordWorkflow("read")

    id1 = Identity(id=1)
    id1.provides.add(UserNeed(1))

    with pytest.raises(MissingWorkflowError):
        assert wp.query_filter(identity=id1) == {}
