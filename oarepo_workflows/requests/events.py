#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Events for workflow requests."""

from __future__ import annotations

import dataclasses
from functools import cached_property
from typing import TYPE_CHECKING

from oarepo_workflows.requests.generators.multiple_entities import (
    MultipleEntitiesGenerator,
)

if TYPE_CHECKING:
    from invenio_records_permissions.generators import Generator


@dataclasses.dataclass
class WorkflowEvent:
    """Class representing a workflow event."""

    submitters: list[Generator] | tuple[Generator]
    """List of submitters to be used for the event.

       The generators supply needs. The user must have at least one of the needs 
       to be able to create a workflow event.
    """

    @cached_property
    def submitter_generator(self) -> Generator:
        """Return the requesters as a single requester generator."""
        return MultipleEntitiesGenerator(self.submitters)
