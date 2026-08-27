#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see https://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Permission explainer for InAnyWorkflow permission generator."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

from oarepo_runtime.services.permission_explainer import ExplainerResult, PermissionExplainer, explain

from oarepo_workflows import FromRecordWorkflow, current_oarepo_workflows
from oarepo_workflows.services.permissions.generators import InAnyWorkflow

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_permissions import RecordPermissionPolicy


class PolicyExplainerMixin:
    """A mixin for policy explainers."""

    def explain_policy(
        self, identity: Identity, permission_policy: RecordPermissionPolicy, message: str
    ) -> ExplainerResult:
        """Explain the policy for the given identity and workflow permission policy."""
        try:
            workflow_needs = permission_policy.needs
        except AttributeError:
            workflow_needs = "<needs could not be computed>"
        try:
            workflow_allows_icon = "✅" if permission_policy.allows(identity) else "❌"
        except AttributeError:
            workflow_allows_icon = "⚠️"

        workflow_result: ExplainerResult = []
        explainer = cast("PermissionExplainer", self)
        workflow_generators = getattr(permission_policy, f"can_{explainer.permission_policy.action}", [])
        for generator in workflow_generators:
            workflow_result.append(explain(identity, permission_policy, generator))

        return [f"{workflow_allows_icon} {message} {workflow_needs}", workflow_result]


class InAnyWorkflowPermissionExplainer(PolicyExplainerMixin, PermissionExplainer):
    """Explainer for InAnyWorkflow permission generator."""

    TYPES = (InAnyWorkflow,)

    @override
    def explain(self, identity: Identity) -> ExplainerResult:
        """Explain the permission generator."""
        ret = super().explain(identity)
        for workflow in current_oarepo_workflows.record_workflows:
            workflow_permission_policy = workflow.permissions(
                self.permission_policy.action, **self.permission_policy.over
            )
            ret.append(self.explain_policy(identity, workflow_permission_policy, f"workflow: {workflow.code}"))
        return ret


class FromRecordWorkflowExplainer(PolicyExplainerMixin, PermissionExplainer):
    """Explainer for FromRecordWorkflow permission generator."""

    TYPES = (FromRecordWorkflow,)

    @override
    def explain(self, identity: Identity) -> ExplainerResult:
        """Explain the permission generator."""
        ret = super().explain(identity)
        generator = cast("FromRecordWorkflow", self.generator)
        over = self.permission_policy.over
        policy = generator._get_permissions_from_workflow(**over)  # noqa SLF001
        _record, workflow, action_name = generator._get_record_workflow_action(  # noqa SLF001
            **{"record": None, **over}
        )
        if policy is not None:
            ret.append(
                self.explain_policy(
                    identity, policy, f"Workflow {workflow.code if workflow else None} action {action_name}"
                )
            )
        return ret
