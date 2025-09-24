#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

import pytest
from invenio_access.permissions import system_identity

from oarepo_workflows.errors import InvalidWorkflowError


def test_change_workflow(workflow_model, location, search_clear):
    draft = workflow_model.Draft.create({})
    draft.parent.workflow = "my_workflow"
    with pytest.raises(InvalidWorkflowError):
        draft.parent.workflow = "non_existing_workflow"
    with pytest.raises(InvalidWorkflowError):
        draft.parent.workflow = None


def test_workflow_read(default_workflow_json, record_service, location, search_clear):
    data = record_service.create(system_identity, default_workflow_json)
    assert data._record.parent.workflow == "my_workflow"  # noqa SLF001
    assert data._record.state == "draft"  # noqa SLF001
