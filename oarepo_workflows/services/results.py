#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_records_resources.services.base.results import ServiceListResult

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask_principal import Identity
    from invenio_records_resources.services.records.schema import ServiceSchemaWrapper


class InMemoryResultList(ServiceListResult):
    """Service result list for storing in memory results.

    Uses resolved objects instead of opensearch hits.

    Note: we cannot use invenio implementation because it requires opensearch hits containing dictionaries with
    data of the resolved objects. We have no way of converting these back to objects via record load and
    serializing them with schema dump. That's why we return them as they are.
    """

    def __init__(
        self,
        identity: Identity,
        results: list[Any],
        schema: ServiceSchemaWrapper,
    ) -> None:
        """Create the list.

        :params identity: an identity that performed the service request
        :params results: the search results
        :params schema: schema to use for serialization of the result entities
        """
        self._identity = identity
        self._results = results
        self._schema = schema

    @property
    def hits(self) -> Generator[dict[str, Any]]:
        """Iterator over the hits."""
        for record in self._results:  # here we can just use the instantiated entity objects
            projection = self._schema.dump(
                record,
                context={
                    "identity": self._identity,
                    "record": record,
                },
            )
            yield projection
