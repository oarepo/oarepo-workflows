import dataclasses
from typing import Type

from flask_babel import LazyString

from . import WorkflowPermissionPolicy
from .requests import WorkflowRequestPolicy
from .services.permissions import DefaultWorkflowPermissions


@dataclasses.dataclass
class Workflow:
    label: str | LazyString
    permission_policy_cls: Type[DefaultWorkflowPermissions]
    request_policy_cls: Type[WorkflowRequestPolicy] = WorkflowRequestPolicy

    def permissions(self, action, **over):
        """Return permission policy for this workflow applicable to the given action."""
        return self.permission_policy_cls(action, **over)

    def requests(self):
        """Return instance of request policy for this workflow."""
        return self.request_policy_cls()

    def __post_init__(self):
        assert not issubclass(self.permission_policy_cls, WorkflowPermissionPolicy)
        assert issubclass(self.permission_policy_cls, DefaultWorkflowPermissions)

        assert issubclass(self.request_policy_cls, WorkflowRequestPolicy)
