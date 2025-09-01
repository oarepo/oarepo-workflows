#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service for reading auto-approve entities.

The implementation is simple as auto approve is just one entity
so there is no need to store it to database/fetch it from the database.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Never, cast, override

from invenio_records_resources.services.base.service import Service
from oarepo_runtime.services.results import RecordItem, RecordList

from oarepo_workflows.resolvers.auto_approve import AutoApprove

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flask_principal import Identity
    from invenio_records_resources.services.base.config import ServiceConfig
    from invenio_records_resources.services.base.results import (
        ServiceItemResult,
        ServiceListResult,
    )


class AutoApproveRecordItem(RecordItem):
    """Single record result for AutoApprove."""

    # TODO: overwrite superclass method or use the furthest base one and implement by demand?
    # has_permissions_to is used in ui?

    def __init__(
        self,
    ):
        """Override constructor to discard unnecesary arguments."""
        self._record = AutoApprove()

    @property
    @override
    def links(self) -> Never:
        """Not used here."""
        raise NotImplementedError

    @property
    @override
    def errors(self) -> list[Never]:  # type: ignore[reportIncompatibleMethodOverride]
        return []

    @property
    @override
    def data(self) -> dict[str, str]:
        """Get the record data.

        Returns:
            dict: The serialized record data.

        """
        return AutoApprove.serialization

    @property
    def id(self) -> Any:
        """Get the record id."""
        return self.data["id"]


class AutoApproveRecordList(RecordList):
    """List autopprove result."""

    def __init__(
        self,
        results: list[AutoApprove],
    ) -> None:
        """Override constructor to discard unnecesary arguments."""
        self._results = results
        self._params = None

    @property
    @override
    def total(self) -> int:
        """Get total number of hits."""
        return len(self._results)

    @property
    @override
    def aggregations(self) -> None:
        """Get the search result aggregations."""
        return None

    # we would have to define self._service.record_cls.loads(hit.to_dict())
    @property
    @override
    def hits(self) -> Any:
        """Get iterator over search result hits.

        Yields:
            dict: The serialized record data for each hit.

        """
        for _ in self._results:
            yield AutoApprove.serialization
        """
        for hit in self._results:
            # Project the record
            projection = self._schema.dump(
                hit,
                context={"identity": self._identity, "record": hit},
            )
            if self._nested_links_item:
                for link in self._nested_links_item:
                    link.expand(self._identity, hit, projection)

            for c in self.components:
                c.update_data(
                    identity=self._identity,
                    record=hit,
                    projection=projection,
                    expand=self._expand,
                )
            yield projection
        """

    """
    @property
    def hits(self):
        for hit in self._results:
            # Load dump
            hit_dict = hit.to_dict()

            try:
                # Project the record
                if hit_dict.get("record_status") == "draft":
                    record = self._service.draft_cls.loads(hit_dict)
                else:
                    record = self._service.record_cls.loads(hit_dict)

                projection = self._schema.dump(
                    record,
                    context=dict(
                        identity=self._identity,
                        record=record,
                    ),
                )
                if hasattr(self._service.config, "links_search_item"):
                    links_tpl = self._service.config.search_item_links_template(
                        self._service.config.links_search_item
                    )
                    projection["links"] = links_tpl.expand(self._identity, record)
                elif self._links_item_tpl:
                    projection["links"] = self._links_item_tpl.expand(
                        self._identity, record
                    )
                # todo optimization viz FieldsResolver
                for c in self.components:
                    c.update_data(
                        identity=self._identity,
                        record=record,
                        projection=projection,
                        expand=self._expand,
                    )
                yield projection
            except Exception:
                # ignore record with error, put it to log so that it gets to glitchtip
                # but don't break the whole search
                log.exception("Error while dumping record %s", hit_dict)
    """


"""
class classproperty[T]:  # noqa N801
    # TODO: move to runtime
    #Class property decorator implementation.

    #Allows defining properties at class level rather than instance level.
    #Will be moved to runtime in future versions.


    def __init__(self, func: Callable):
        #Initialize the class property
        self.fget = func

    def __get__(self, instance: Any, owner: Any) -> T:
        # Get the value of the class property
        return self.fget(owner)


def entity_schema_factory(keyword: str, entity: type) -> type:

    @post_load
    def _make(self, **kwargs: Any) -> Any:  # noqa ARG001, ANN001
        return entity(**kwargs)

    flds = {
        "keyword": fields.String(dump_only=True, dump_default=keyword),
        "id": fields.String(dump_only=True, dump_default="true"),
        "_make": _make,
    }
    return type(f"{keyword.capitalize()}Schema", (Schema,), flds)
"""


class AutoApproveService(Service):
    """Service implementation for named entities.

    Provides concrete implementation of read operations for named entities
    that don't require database storage.
    """

    def __init__(self):
        """Override constructor to discard unnecesary arguments."""

    @property
    def config(self) -> ServiceConfig:
        """Get fake service config."""
        return cast("ServiceConfig", SimpleNamespace(service_id="auto_approve"))

    def read(self, identity: Identity, id_: str, **kwargs: Any) -> ServiceItemResult:  # noqa ARG002
        """Read a single auto-approve record.

        Args:
            identity: The identity requesting access.
            id_: The record ID.
            **kwargs: Additional keyword arguments.

        Returns:
            ServiceItemResult: The auto-approve record.

        """
        return AutoApproveRecordItem()

    def read_many(
        self,
        identity: Identity,  # noqa ARG002
        ids: Iterable[str],
        fields: Iterable[str] | None = None,  # noqa ARG002
        **kwargs: Any,  # noqa ARG002
    ) -> ServiceListResult:
        """Read multiple auto-approve records.

        Args:
            identity: The identity requesting access.
            ids: Iterable of record IDs.
            fields: Optional fields to include in the result.
            **kwargs: Additional keyword arguments.

        Returns:
            ServiceListResult: List of auto-approve records.

        """
        return AutoApproveRecordList([AutoApprove() for _ in ids])


"""
class AutoApproveEntityServiceConfig:


    service_id = "auto_approve"
"""
