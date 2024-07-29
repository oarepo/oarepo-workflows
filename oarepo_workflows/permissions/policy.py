from functools import reduce

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)
from invenio_search.engine import dsl
from oarepo_runtime.services.generators import RecordOwners

from oarepo_workflows.permissions.generators import WorkflowPermission

from ..proxies import current_oarepo_workflows
from .generators import IfInState


class DefaultWorkflowPermissionPolicy(RecordPermissionPolicy):
    PERMISSIONS_REMAP = {
        "read_draft": "read",
        "update_draft": "update",
        "delete_draft": "delete",
        "draft_create_files": "create_files",
        "draft_set_content_files": "set_content_files",
        "draft_get_content_files": "get_content_files",
        "draft_commit_files": "commit_files",
        "draft_read_files": "read_files",
        "draft_update_files": "update_files",
        "search_drafts": "search",
    }

    system_process = SystemProcess()

    def __init__(self, action_name=None, **over):
        action_name = DefaultWorkflowPermissionPolicy.PERMISSIONS_REMAP.get(
            action_name, action_name
        )
        can = getattr(self, f"can_{action_name}")
        # todo check if needed
        if self.system_process not in can:
            can.append(self.system_process)
        super().__init__(action_name, **over)

    can_read = [
        IfInState("draft", [RecordOwners()]),
        IfInState("published", [AuthenticatedUser()]),
    ]
    can_update = [IfInState("draft", [RecordOwners()])]
    can_delete = [
        IfInState("draft", [RecordOwners()]),
    ]
    can_create = [AuthenticatedUser()]
    can_publish = [AuthenticatedUser()]


class WorkflowPermissionPolicy(RecordPermissionPolicy):
    can_create = [WorkflowPermission("create")]
    can_publish = [WorkflowPermission("publish")]
    can_search = [SystemProcess(), AnyUser()]
    can_read = [WorkflowPermission("read")]
    can_update = [WorkflowPermission("update")]
    can_delete = [WorkflowPermission("delete")]
    can_create_files = [WorkflowPermission("create_files")]
    can_set_content_files = [WorkflowPermission("set_content_files")]
    can_get_content_files = [WorkflowPermission("get_content_files")]
    can_commit_files = [WorkflowPermission("commit_files")]
    can_read_files = [WorkflowPermission("read_files")]
    can_update_files = [WorkflowPermission("update_files")]
    can_edit = [WorkflowPermission("edit")]

    can_search_drafts = [SystemProcess(), AnyUser()]
    can_read_draft = [WorkflowPermission("read")]
    can_update_draft = [WorkflowPermission("update")]
    can_delete_draft = [WorkflowPermission("delete")]
    can_draft_create_files = [WorkflowPermission("create_files")]
    can_draft_set_content_files = [WorkflowPermission("set_content_files")]
    can_draft_get_content_files = [WorkflowPermission("get_content_files")]
    can_draft_commit_files = [WorkflowPermission("commit_files")]
    can_draft_read_files = [WorkflowPermission("read_files")]
    can_draft_update_files = [WorkflowPermission("update_files")]

    @property
    def query_filters(self):
        if not (self.action == "read" or self.action == "read_draft"):
            return super().query_filters
        workflows = current_oarepo_workflows.record_workflows
        queries = []
        for workflow_id, workflow in workflows.items():
            q_inworkflow = dsl.Q("term", **{"parent.workflow": workflow_id})
            workflow_filters = workflow.permissions(
                self.action, **self.over
            ).query_filters
            if not workflow_filters:
                workflow_filters = [dsl.Q("match_none")]
            query = reduce(lambda f1, f2: f1 | f2, workflow_filters) & q_inworkflow
            queries.append(query)
        return [q for q in queries if q]
