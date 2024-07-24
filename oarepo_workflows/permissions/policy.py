from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess, AnyUser
from oarepo_runtime.services.generators import RecordOwners
from oarepo_workflows.permissions.generators import WorkflowPermission
from .generators import IfInState
from ..proxies import current_oarepo_workflows
from invenio_search.engine import dsl
import operator
from functools import reduce


class DefaultWorkflowPermissionPolicy(RecordPermissionPolicy):
    PERMISSIONS_REMAP = {
        "can_read_draft": "can_read",
        "can_update_draft": "can_update",
        "can_delete_draft": "can_delete",
        "can_draft_create_files": "can_create_files",
        "can_draft_set_content_files": "can_set_content_files",
        "can_draft_get_content_files": "can_get_content_files",
        "can_draft_commit_files": "can_commit_files",
        "can_draft_read_files": "can_read_files",
        "can_draft_update_files": "can_update_files",
        "can_search_drafts": "can_search",
    }

    system_process = SystemProcess()

    def __init__(self, action_name=None, **over):
        action_name = DefaultWorkflowPermissionPolicy.PERMISSIONS_REMAP.get(
            action_name, action_name
        )
        can = getattr(self, action_name)
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
    can_create = [WorkflowPermission("can_create")]
    can_publish = [WorkflowPermission("can_publish")]
    can_search = [SystemProcess(), AnyUser()]
    can_read = [WorkflowPermission("can_read")]
    can_update = [WorkflowPermission("can_update")]
    can_delete = [WorkflowPermission("can_delete")]
    can_create_files = [WorkflowPermission("can_create_files")]
    can_set_content_files = [WorkflowPermission("can_set_content_files")]
    can_get_content_files = [WorkflowPermission("can_get_content_files")]
    can_commit_files = [WorkflowPermission("can_commit_files")]
    can_read_files = [WorkflowPermission("can_read_files")]
    can_update_files = [WorkflowPermission("can_update_files")]
    can_edit = [WorkflowPermission("can_edit")]

    can_search_drafts = [SystemProcess(), AnyUser()]
    can_read_draft = [WorkflowPermission("can_read")]
    can_update_draft = [WorkflowPermission("can_update")]
    can_delete_draft = [WorkflowPermission("can_delete")]
    can_draft_create_files = [WorkflowPermission("can_create_files")]
    can_draft_set_content_files = [WorkflowPermission("can_set_content_files")]
    can_draft_get_content_files = [WorkflowPermission("can_get_content_files")]
    can_draft_commit_files = [WorkflowPermission("can_commit_files")]
    can_draft_read_files = [WorkflowPermission("can_read_files")]
    can_draft_update_files = [WorkflowPermission("can_update_files")]

    @property
    def query_filters(self):
        if self.action != "read" and self.action != "read_draft":
            return super().query_filters
        workflows = current_oarepo_workflows.record_workflows.keys()
        queries = []
        for workflow in workflows:
            q_inworkflow = dsl.Q("match", **{"parent.workflow": workflow})
            query = WorkflowPermission("can_read").query_filter(data={"parent": {"workflow_id": workflow}}, **self.over) & q_inworkflow
            queries.append(query)
        return [q for q in queries if q]

