from functools import reduce

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    Disable,
    SystemProcess,
)
from invenio_search.engine import dsl
from oarepo_runtime.services.generators import RecordOwners

from ...proxies import current_oarepo_workflows
from .generators import IfInState, SameAs, WorkflowPermission
from typing import Optional


class DefaultWorkflowPermissions(RecordPermissionPolicy):
    """
    Base class for workflow permissions, subclass from it and put the result to Workflow constructor.
    Example:
        class MyWorkflowPermissions(DefaultWorkflowPermissions):
            can_read = [AnyUser()]
    in invenio.cfg
    WORKFLOWS = {
        'default': Workflow(
            permission_policy_cls = MyWorkflowPermissions, ...
        )
    }
    """

    # new version - update; edit current version - disable -> idk if there's other way than something like IfNoEditDraft/IfNoNewVersionDraft generators-

    files_edit = [
        IfInState("draft", [RecordOwners()]),
        IfInState("published", [Disable()]),
    ]

    system_process = SystemProcess()

    def __init__(self, action_name: Optional[str]=None, **over) -> None:
        can = getattr(self, f"can_{action_name}")
        if self.system_process not in can:
            can.append(self.system_process)
        over["policy"] = self
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
    can_new_version = [AuthenticatedUser()]

    can_create_files = [SameAs("files_edit")]
    can_set_content_files = [SameAs("files_edit")]
    can_commit_files = [SameAs("files_edit")]
    can_update_files = [SameAs("files_edit")]
    can_delete_files = [SameAs("files_edit")]
    can_draft_create_files = [SameAs("files_edit")]
    can_read_files = [SameAs("can_read")]
    can_get_content_files = [SameAs("can_read")]

    can_read_draft = [SameAs("can_read")]
    can_update_draft = [SameAs("can_update")]
    can_delete_draft = [SameAs("can_delete")]


class WorkflowPermissionPolicy(RecordPermissionPolicy):
    """
    Permission policy to be used in permission presets directly on RecordServiceConfig.permission_policy_cls
    Do not use this class in Workflow constructor.
    """

    can_create = [WorkflowPermission("create")]
    can_publish = [WorkflowPermission("publish")]
    can_read = [WorkflowPermission("read")]
    can_update = [WorkflowPermission("update")]
    can_delete = [WorkflowPermission("delete")]
    can_create_files = [WorkflowPermission("create_files")]
    can_set_content_files = [WorkflowPermission("set_content_files")]
    can_get_content_files = [WorkflowPermission("get_content_files")]
    can_commit_files = [WorkflowPermission("commit_files")]
    can_read_files = [WorkflowPermission("read_files")]
    can_update_files = [WorkflowPermission("update_files")]
    can_delete_files = [WorkflowPermission("delete_files")]

    can_read_draft = [WorkflowPermission("read_draft")]
    can_update_draft = [WorkflowPermission("update_draft")]
    can_delete_draft = [WorkflowPermission("delete_draft")]
    can_edit = [WorkflowPermission("edit")]
    can_new_version = [WorkflowPermission("new_version")]
    can_draft_create_files = [WorkflowPermission("draft_create_files")]

    can_search = [SystemProcess(), AnyUser()]
    can_search_drafts = [SystemProcess(), AnyUser()]
    can_search_versions = [SystemProcess(), AnyUser()]

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
