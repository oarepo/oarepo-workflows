from invenio_records.dictutils import dict_lookup
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess
from oarepo_runtime.services.generators import RecordOwners

from oarepo_workflows.proxies import current_oarepo_workflows
import copy
from .generators import IfInState


# todo this must be used as permission_policy_cls in model's service config and for now is not compatible with permissions presets - the mixin must be deleted
def workflow_permission_set_getter(service, action_name=None, **kwargs):
    if "record" in kwargs: # todo should the input to get_default_workflow be always parent? it should be unified somewhere
        kwargs_copy = copy.deepcopy(kwargs)
        record = kwargs_copy.pop("record")
        parent = record.parent
        if "workflow" in parent:
            workflow_id = parent["workflow"]
        else:
            workflow_id = current_oarepo_workflows.get_default_workflow(record=parent, **kwargs_copy)
    else:
        # todo hook in communities to get default for community
        workflow_id = current_oarepo_workflows.get_default_workflow(**kwargs)
    try:
        policy = dict_lookup(
            current_oarepo_workflows.record_workflows, f"{workflow_id}.permissions"
        )
    except:
        #todo dev debug
        print()
    return policy(action_name, **kwargs)


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
        "search_drafts": "search"
    }

    def __init__(self, action_name=None, **over):
        action_name = WorkflowPermissionPolicy.PERMISSIONS_REMAP.get(action_name, action_name)
        can = getattr(self, f"can_{action_name}")
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
