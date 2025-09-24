#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Generator that combines multiple generators together with an 'or' operation."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, override

from ...resolvers.multiple_entities import MultipleEntitiesEntity
from ...services.permissions.generators import AggregateGenerator
from .recipient_generator import RecipientGeneratorMixin

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from invenio_records_permissions.generators import Generator as InvenioGenerator
    from invenio_records_resources.records.api import Record
    from invenio_requests.customizations.request_types import RequestType


@dataclasses.dataclass
class MultipleEntitiesGenerator(RecipientGeneratorMixin, AggregateGenerator):
    """A generator that combines multiple generators with 'or' operation."""

    generators: Sequence[InvenioGenerator]
    """List of generators to be combined."""

    @override
    def _generators(self, **context: Any) -> Sequence[InvenioGenerator]:
        """Return the generators."""
        return self.generators

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:
        """Return the reference receiver(s) of the request.

        This call requires the context to contain at least "record" and "request_type"

        Must return a list of dictionary serialization of the receivers.

        Might return empty list or None to indicate that the generator does not
        provide any receivers.
        """
        references = []

        for generator in self.generators:
            if not isinstance(generator, RecipientGeneratorMixin):
                raise TypeError(
                    f"Generator {generator} is not a recipient generator and can not be used in "
                    f"MultipleGeneratorsGenerator."
                )

            generator_references = generator.reference_receivers(record=record, request_type=request_type, **context)
            if generator_references:
                references.extend(generator_references)
        if not references:
            return []
        if len(references) == 1:
            return references

        return [{"multiple": MultipleEntitiesEntity.create_id(references)}]
