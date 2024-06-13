from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    SystemProcess,
)



class WorkflowPermissionPolicy(RecordPermissionPolicy):

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
    }

    def __init__(self, action, **over):
        action = WorkflowPermissionPolicy.PERMISSIONS_REMAP.get(action, action)
        super().__init__(action, **over)