#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service components for supporting workflows on Invenio records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from invenio_records_resources.services.records.components.base import ServiceComponent

from oarepo_workflows.errors import MissingWorkflowError
from oarepo_workflows.proxies import current_oarepo_workflows

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.records import Record


class WorkflowSetupComponent(ServiceComponent):
    pass


class WorkflowComponent(ServiceComponent):
    """Workflow component.

    This component is responsible for checking if the workflow is defined in the input data
    when record is created. If it is not present, it raises an error.
    """

    depends_on = [WorkflowSetupComponent]
    affects = "*"
    # put it before metadata component to make sure that the workflow
    # is set at the beginning of the record creation process. This makes sure
    # that for example file checks are done with the correct workflow set.

    def create(
        self,
        identity: Identity,
        data: Optional[dict[str, Any]] = None,
        record: Optional[Record] = None,
        **kwargs: Any,
    ) -> None:
        """Implement record creation checks and set the workflow on the created record."""
        if not data:
            # sanity check, should be handled by policy before the component is called
            raise MissingWorkflowError(
                "Workflow not defined in input. As this should be handled by a policy, "
                "make sure you are using workflow-enabled policy.",
                record=data,
            )  # pragma: no cover
        try:
            workflow_id = data["parent"]["workflow"]
        except KeyError as e:  # pragma: no cover
            # sanity check, should be handled by policy before the component is called
            raise MissingWorkflowError(  # pragma: no cover
                "Workflow not defined in input. As this should be handled by a policy, "
                "make sure you are using workflow-enabled policy.",
                record=data,
            ) from e

        current_oarepo_workflows.set_workflow(
            identity, record, workflow_id, uow=self.uow, **kwargs
        )
