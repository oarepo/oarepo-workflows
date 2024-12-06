#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Record policy for workflows."""

from __future__ import annotations

from functools import reduce

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    SystemProcess,
)
from invenio_search.engine import dsl

from ...proxies import current_oarepo_workflows
from .generators import FromRecordWorkflow


class WorkflowRecordPermissionPolicy(RecordPermissionPolicy):
    """Permission policy to be used in permission presets directly on RecordServiceConfig.permission_policy_cls.

    Do not use this class in Workflow constructor.
    """

    can_create = [FromRecordWorkflow("create")]
    can_publish = [FromRecordWorkflow("publish")]
    can_read = [FromRecordWorkflow("read")]
    can_update = [FromRecordWorkflow("update")]
    can_delete = [FromRecordWorkflow("delete")]
    can_create_files = [FromRecordWorkflow("create_files")]
    can_set_content_files = [FromRecordWorkflow("set_content_files")]
    can_get_content_files = [FromRecordWorkflow("get_content_files")]
    can_commit_files = [FromRecordWorkflow("commit_files")]
    can_read_files = [FromRecordWorkflow("read_files")]
    can_update_files = [FromRecordWorkflow("update_files")]
    can_delete_files = [FromRecordWorkflow("delete_files")]
    can_list_files = [FromRecordWorkflow("list_files")]

    can_read_draft = [FromRecordWorkflow("read_draft")]
    can_update_draft = [FromRecordWorkflow("update_draft")]
    can_delete_draft = [FromRecordWorkflow("delete_draft")]
    can_edit = [FromRecordWorkflow("edit")]
    can_new_version = [FromRecordWorkflow("new_version")]
    can_draft_create_files = [FromRecordWorkflow("draft_create_files")]

    can_search = [SystemProcess(), AnyUser()]
    can_search_drafts = [SystemProcess(), AnyUser()]
    can_search_versions = [SystemProcess(), AnyUser()]

    @property
    def query_filters(self) -> list[dict]:
        """Return query filters from the delegated workflow permissions."""
        if not (self.action == "read" or self.action == "read_draft"):
            return super().query_filters
        workflows = current_oarepo_workflows.record_workflows
        queries = []
        for workflow_id, workflow in workflows.items():
            q_in_workflow = dsl.Q("term", **{"parent.workflow": workflow_id})
            workflow_filters = workflow.permissions(
                self.action, **self.over
            ).query_filters
            if not workflow_filters:
                workflow_filters = [dsl.Q("match_none")]
            query = reduce(lambda f1, f2: f1 | f2, workflow_filters) & q_in_workflow
            queries.append(query)
        return [q for q in queries if q]
