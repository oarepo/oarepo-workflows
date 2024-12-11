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
import json
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional, override

from invenio_records_permissions.generators import Generator

from .recipient_generator import RecipientGeneratorMixin

if TYPE_CHECKING:
    from flask_principal import Need
    from invenio_records_resources.records.api import Record
    from invenio_requests.customizations.request_types import RequestType


@dataclasses.dataclass
class MultipleEntitiesGenerator(RecipientGeneratorMixin, Generator):
    """A generator that combines multiple generators with 'or' operation."""

    generators: list[Generator] | tuple[Generator]
    """List of generators to be combined."""

    @override
    def needs(self, **context: Any) -> set[Need]:
        """Generate a set of needs from generators that a person needs to have.

        :param context: Context.
        :return: Set of needs.
        """
        return {
            need for generator in self.generators for need in generator.needs(**context)
        }

    @override
    def excludes(self, **context: Any) -> set[Need]:
        """Generate a set of needs that person must not have.

        :param context: Context.
        :return: Set of needs.
        """
        return {
            exclude
            for generator in self.generators
            for exclude in generator.excludes(**context)
        }

    @override
    def query_filter(self, **context: Any) -> list[dict]:
        """Generate a list of opensearch query filters.

         These filters are used to filter objects. These objects are governed by a policy
         containing this generator.

        :param context: Context.
        """
        ret: list[dict] = []
        for generator in self.generators:
            query_filter = generator.query_filter(**context)
            if query_filter:
                if isinstance(query_filter, Iterable):
                    ret.extend(query_filter)
                else:
                    ret.append(query_filter)
        return ret

    @override
    def reference_receivers(
        self,
        record: Optional[Record] = None,
        request_type: Optional[RequestType] = None,
        **context: Any,
    ) -> list[dict[str, str]]:  # pragma: no cover
        """Return the reference receiver(s) of the request.

        This call requires the context to contain at least "record" and "request_type"

        Must return a list of dictionary serialization of the receivers.

        Might return empty list or None to indicate that the generator does not
        provide any receivers.
        """
        references = []

        for generator in self.generators:
            if not isinstance(generator, RecipientGeneratorMixin):
                raise ValueError(
                    f"Generator {generator} is not a recipient generator and can not be used in "
                    f"MultipleGeneratorsGenerator."
                )

            reference = generator.reference_receivers(
                record=record, request_type=request_type, **context
            )
            if reference:
                references.extend(reference)
        if not references:
            return []
        if len(references) == 1:
            return references

        return [{"multiple": json.dumps(references)}]
