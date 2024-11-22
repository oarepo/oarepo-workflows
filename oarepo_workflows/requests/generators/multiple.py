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
from typing import TYPE_CHECKING, Any, Iterable

from invenio_records_permissions.generators import Generator

if TYPE_CHECKING:
    from flask_principal import Need


@dataclasses.dataclass
class MultipleGeneratorsGenerator(Generator):
    """A generator that combines multiple generators with 'or' operation."""

    generators: list[Generator] | tuple[Generator]
    """List of generators to be combined."""

    def needs(self, **context: Any) -> set[Need]:
        """Generate a set of needs from generators that a person needs to have.

        :param context: Context.
        :return: Set of needs.
        """
        return {
            need for generator in self.generators for need in generator.needs(**context)
        }

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
