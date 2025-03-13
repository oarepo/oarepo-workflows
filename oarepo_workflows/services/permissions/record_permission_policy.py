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

    can_commit_files = [FromRecordWorkflow("commit_files")]
    can_create = [FromRecordWorkflow("create")]
    can_create_files = [FromRecordWorkflow("create_files")]
    can_delete = [FromRecordWorkflow("delete")]
    can_delete_draft = [FromRecordWorkflow("delete_draft")]
    can_delete_files = [FromRecordWorkflow("delete_files")]
    can_draft_create_files = [FromRecordWorkflow("draft_create_files")]
    can_edit = [FromRecordWorkflow("edit")]
    can_get_content_files = [FromRecordWorkflow("get_content_files")]
    can_list_files = [FromRecordWorkflow("list_files")]
    can_new_version = [FromRecordWorkflow("new_version")]
    can_publish = [FromRecordWorkflow("publish")]
    can_read = [FromRecordWorkflow("read")]
    can_read_all_records = [FromRecordWorkflow("read_all_records")]
    can_read_deleted = [FromRecordWorkflow("read_deleted")]
    can_read_draft = [FromRecordWorkflow("read_draft")]
    can_read_files = [FromRecordWorkflow("read_files")]
    can_search = [SystemProcess(), AnyUser()]
    can_search_drafts = [SystemProcess(), AnyUser()]
    can_search_versions = [SystemProcess(), AnyUser()]
    can_search_all_records = [SystemProcess(), AnyUser()]
    can_set_content_files = [FromRecordWorkflow("set_content_files")]
    can_update = [FromRecordWorkflow("update")]
    can_update_draft = [FromRecordWorkflow("update_draft")]
    can_update_files = [FromRecordWorkflow("update_files")]

    # extra from rdm - some of these might we might ignore, but adding them here
    # will not break anything
    can_add_community = [FromRecordWorkflow("add_community")]
    can_bulk_add = [FromRecordWorkflow("bulk_add")]
    can_draft_commit_files = [FromRecordWorkflow("draft_commit_files")]
    can_draft_delete_files = [FromRecordWorkflow("draft_delete_files")]
    can_draft_get_content_files = [FromRecordWorkflow("draft_get_content_files")]
    can_draft_media_commit_files = [FromRecordWorkflow("draft_media_commit_files")]
    can_draft_media_create_files = [FromRecordWorkflow("draft_media_create_files")]
    can_draft_media_delete_files = [FromRecordWorkflow("draft_media_delete_files")]
    can_draft_media_get_content_files = [
        FromRecordWorkflow("draft_media_get_content_files")
    ]
    can_draft_media_read_files = [FromRecordWorkflow("draft_media_read_files")]
    can_draft_media_set_content_files = [
        FromRecordWorkflow("draft_media_set_content_files")
    ]
    can_draft_media_update_files = [FromRecordWorkflow("draft_media_update_files")]
    can_draft_read_files = [FromRecordWorkflow("draft_read_files")]
    can_draft_set_content_files = [FromRecordWorkflow("draft_set_content_files")]
    can_draft_update_files = [FromRecordWorkflow("draft_update_files")]
    can_lift_embargo = [FromRecordWorkflow("lift_embargo")]
    can_manage = [FromRecordWorkflow("manage")]
    can_manage_files = [FromRecordWorkflow("manage_files")]
    can_manage_internal = [FromRecordWorkflow("manage_internal")]
    can_manage_quota = [FromRecordWorkflow("manage_quota")]
    can_manage_record_access = [FromRecordWorkflow("manage_record_access")]
    can_media_commit_files = [FromRecordWorkflow("media_commit_files")]
    can_media_create_files = [FromRecordWorkflow("media_create_files")]
    can_media_delete_files = [FromRecordWorkflow("media_delete_files")]
    can_media_get_content_files = [FromRecordWorkflow("media_get_content_files")]
    can_media_read_deleted_files = [FromRecordWorkflow("media_read_deleted_files")]
    can_media_read_files = [FromRecordWorkflow("media_read_files")]
    can_media_set_content_files = [FromRecordWorkflow("media_set_content_files")]
    can_media_update_files = [FromRecordWorkflow("media_update_files")]
    can_moderate = [FromRecordWorkflow("moderate")]
    can_pid_create = [FromRecordWorkflow("pid_create")]
    can_pid_delete = [FromRecordWorkflow("pid_delete")]
    can_pid_discard = [FromRecordWorkflow("pid_discard")]
    can_pid_manage = [FromRecordWorkflow("pid_manage")]
    can_pid_register = [FromRecordWorkflow("pid_register")]
    can_pid_update = [FromRecordWorkflow("pid_update")]
    can_preview = [FromRecordWorkflow("preview")]
    can_purge = [FromRecordWorkflow("purge")]
    can_query_stats = [FromRecordWorkflow("query_stats")]
    can_read_deleted_files = [FromRecordWorkflow("read_deleted_files")]
    can_remove_community = [FromRecordWorkflow("remove_community")]
    can_remove_record = [FromRecordWorkflow("remove_record")]
    can_review = [FromRecordWorkflow("review")]
    can_view = [FromRecordWorkflow("view")]

    @property
    def query_filters(self) -> list[dict]:
        """Return query filters from the delegated workflow permissions."""
        if self.action not in (
            "read",
            "read_draft",
            "read_deleted",
            "read_all_records",
        ):
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
