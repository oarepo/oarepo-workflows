import dataclasses
from typing import Type

from flask_babel import LazyString

from .permissions import DefaultWorkflowPermissionPolicy
from .requests import WorkflowRequestPolicy


@dataclasses.dataclass
class Workflow:
    label: str | LazyString
    permissions_cls: Type[DefaultWorkflowPermissionPolicy]
    requests_cls: Type[WorkflowRequestPolicy] = WorkflowRequestPolicy

    @property
    def permissions(self):
        return self.permissions_cls

    @property
    def requests(self):
        return self.requests_cls()
