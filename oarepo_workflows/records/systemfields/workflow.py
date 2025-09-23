#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Workflow system field."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from invenio_records.systemfields.model import ModelField
from oarepo_runtime.records.systemfields import MappingSystemFieldMixin

from oarepo_workflows import current_oarepo_workflows
from oarepo_workflows.errors import InvalidWorkflowError

if TYPE_CHECKING:
    from invenio_records.models import RecordMetadataBase


class WithWorkflow(Protocol):
    """A protocol for a record's parent containing a workflow field.

    Later on, if typing.Intersection is implemented,
    one could use it to have the record correctly typed as
    record: Intersection[WithWorkflow, ParentRecord]
    """

    workflow: str
    """Workflow of the record."""


class WorkflowField(MappingSystemFieldMixin, ModelField):
    """Workflow system field, should be defined on ParentRecord."""

    def __init__(self) -> None:
        """Initialize the workflow field."""
        self._workflow = None  # added in db
        super().__init__(model_field_name="workflow", key="workflow")

    def _set(self, model: RecordMetadataBase, value: str) -> None:
        """Set the workflow on the model's field."""
        if value not in current_oarepo_workflows.workflow_by_code:
            raise InvalidWorkflowError(
                f"Workflow {value} does not exist in the configuration.",
            )
        super()._set(model, value)
