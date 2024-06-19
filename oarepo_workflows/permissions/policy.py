from invenio_records.dictutils import dict_lookup
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess
from oarepo_runtime.services.generators import RecordOwners

from oarepo_workflows.proxies import current_oarepo_workflows

from .generators import IfInState


# todo this must be used as permission_policy_cls in model's service config and for now is not compatible with permissions presets - the mixin must be deleted
def workflow_permission_set_getter(service, action, **kwargs):
    if "record" in kwargs:
        workflow_id = kwargs["record"].parent["workflow"]
    else:
        # todo hook in communities to get default for community
        workflow_id = "default"
    policy = dict_lookup(
        current_oarepo_workflows.record_workflows, f"{workflow_id}.permissions"
    )
    return policy(action, **kwargs)


# todo this is just for testing purposes now
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

    can_search = [SystemProcess(), AuthenticatedUser()]
    can_read = [
        IfInState("draft", [SystemProcess(), RecordOwners()]),
        IfInState("published", [SystemProcess(), AuthenticatedUser()]),
    ]
    can_update = [IfInState("draft", RecordOwners()), SystemProcess()]
    can_delete = [
        IfInState("draft", RecordOwners()),
        # published record can not be deleted directly by anyone else than system
        SystemProcess(),
    ]
    can_create = [SystemProcess(), AuthenticatedUser()]
    can_publish = [SystemProcess(), AuthenticatedUser()]
