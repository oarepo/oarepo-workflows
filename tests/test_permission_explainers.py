#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see https://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for oarepo_workflows.services.permissions.explainers."""

from __future__ import annotations

from flask_principal import Identity, UserNeed
from invenio_records_permissions import RecordPermissionPolicy
from oarepo_runtime.services.permission_explainer import format_explanation

from oarepo_workflows import current_oarepo_workflows
from oarepo_workflows.services.permissions.explainers import (
    FromRecordWorkflowExplainer,
    InAnyWorkflowPermissionExplainer,
)
from oarepo_workflows.services.permissions.generators import FromRecordWorkflow, InAnyWorkflow


class SampleWorkflowPolicy(RecordPermissionPolicy):
    """Permission policy exercising the workflow explainers."""

    can_read = (InAnyWorkflow("read"),)
    can_from_record = (FromRecordWorkflow("read"),)


def _identity(user_id: int) -> Identity:
    i = Identity(user_id)
    i.provides.add(UserNeed(user_id))
    return i


def test_in_any_workflow_explainer_lists_each_workflow(app, users, search_clear):
    policy = SampleWorkflowPolicy("read")
    generator = SampleWorkflowPolicy.can_read[0]

    result = InAnyWorkflowPermissionExplainer(policy, generator).explain(_identity(1))

    assert result[0].startswith(("✅ InAnyWorkflow", "❌ InAnyWorkflow", "⚠️ InAnyWorkflow"))

    formatted = format_explanation(result)
    for workflow in current_oarepo_workflows.record_workflows:
        assert f"workflow: {workflow.code}" in formatted


def test_in_any_workflow_explainer_allows_matching_user_in_specific_workflow(app, users, search_clear):
    """different_read_1 workflow explicitly grants access to user1@example.org via UserGenerator."""
    policy = SampleWorkflowPolicy("read")
    generator = SampleWorkflowPolicy.can_read[0]
    user1 = users[0]

    result = InAnyWorkflowPermissionExplainer(policy, generator).explain(user1.identity)

    formatted = format_explanation(result)
    assert "✅ workflow: different_read_1" in formatted
    assert "UserGenerator" in formatted


def test_in_any_workflow_explainer_denies_unrelated_user(app, users, search_clear):
    policy = SampleWorkflowPolicy("read")
    generator = SampleWorkflowPolicy.can_read[0]
    user2 = users[1]

    result = InAnyWorkflowPermissionExplainer(policy, generator).explain(user2.identity)

    formatted = format_explanation(result)
    assert "❌ workflow: different_read_1" in formatted
    assert "❌ workflow: different_read_2" in formatted


def test_from_record_workflow_explainer_defaults_to_default_workflow(app, search_clear):
    """Without a workflow code in the data, the default workflow ('individual') is used."""
    policy = SampleWorkflowPolicy("read", data={})
    generator = SampleWorkflowPolicy.can_from_record[0]

    result = FromRecordWorkflowExplainer(policy, generator).explain(_identity(1))

    formatted = format_explanation(result)
    assert "Workflow individual action read" in formatted


def test_from_record_workflow_explainer_uses_workflow_from_data(app, users, search_clear):
    policy = SampleWorkflowPolicy("read", data={"parent": {"workflow": "different_read_1"}})
    generator = SampleWorkflowPolicy.can_from_record[0]
    user1 = users[0]

    result = FromRecordWorkflowExplainer(policy, generator).explain(user1.identity)

    formatted = format_explanation(result)
    assert "✅ Workflow different_read_1 action read" in formatted
    assert "UserGenerator" in formatted


def test_from_record_workflow_explainer_denies_excluded_user(app, users, search_clear):
    policy = SampleWorkflowPolicy("read", data={"parent": {"workflow": "different_read_1"}})
    generator = SampleWorkflowPolicy.can_from_record[0]
    user3 = users[2]

    result = FromRecordWorkflowExplainer(policy, generator).explain(user3.identity)

    formatted = format_explanation(result)
    assert "❌ Workflow different_read_1 action read" in formatted


def test_from_record_workflow_explainer_unknown_workflow_code_skips_policy(app, search_clear):
    """An unregistered workflow code cannot be resolved, so no nested explanation is appended."""
    policy = SampleWorkflowPolicy("read", data={"parent": {"workflow": "does-not-exist"}})
    generator = SampleWorkflowPolicy.can_from_record[0]

    result = FromRecordWorkflowExplainer(policy, generator).explain(_identity(1))

    # only the base FromRecordWorkflow line is present, no nested "Workflow <code> action ..." entry
    assert len(result) == 1
    assert result[0].startswith("❌ FromRecordWorkflow")
