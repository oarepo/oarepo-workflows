
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess
from oarepo_runtime.services.generators import RecordOwners

from oarepo_workflows.permissions.generators import WorkflowPermission

from .generators import IfInState


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

    def __init__(self, action_name=None, **over):
        action_name = DefaultWorkflowPermissionPolicy.PERMISSIONS_REMAP.get(
            action_name, action_name
        )
        can = getattr(self, action_name)
        can.append(SystemProcess())
        super().__init__(action_name, **over)

    can_search = [AuthenticatedUser()]
    can_read = [
        IfInState("draft", [RecordOwners()]),
        IfInState("published", [AuthenticatedUser()]),
    ]
    can_update = [IfInState("draft", RecordOwners())]
    can_delete = [
        IfInState("draft", RecordOwners()),
        # published record can not be deleted directly by anyone else than system
        SystemProcess(),
    ]
    can_create = [AuthenticatedUser()]
    can_publish = [AuthenticatedUser()]


class WorkflowPermissionPolicy(RecordPermissionPolicy):

    can_create = [WorkflowPermission("can_create")]
    can_publish = [WorkflowPermission("can_publish")]
    can_search = [WorkflowPermission("can_search")]
    can_read = [WorkflowPermission("can_read")]
    can_update = [WorkflowPermission("can_update")]
    can_delete = [WorkflowPermission("can_delete")]
    can_create_files = [WorkflowPermission("can_create_files")]
    can_set_content_files = [WorkflowPermission("can_set_content_files")]
    can_get_content_files = [WorkflowPermission("can_get_content_files")]
    can_commit_files = [WorkflowPermission("can_commit_files")]
    can_read_files = [WorkflowPermission("can_read_files")]
    can_update_files = [WorkflowPermission("can_update_files")]

    can_search_drafts = [WorkflowPermission("can_search")]
    can_read_draft = [WorkflowPermission("can_read")]
    can_update_draft = [WorkflowPermission("can_update")]
    can_delete_draft = [WorkflowPermission("can_delete")]
    can_draft_create_files = [WorkflowPermission("can_create_files")]
    can_draft_set_content_files = [WorkflowPermission("can_set_content_files")]
    can_draft_get_content_files = [WorkflowPermission("can_get_content_files")]
    can_draft_commit_files = [WorkflowPermission("can_commit_files")]
    can_draft_read_files = [WorkflowPermission("can_read_files")]
    can_draft_update_files = [WorkflowPermission("can_update_files")]
