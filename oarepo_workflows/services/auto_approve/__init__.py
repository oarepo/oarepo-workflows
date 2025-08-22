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

import abc
from typing import TYPE_CHECKING, Any, ClassVar, override

from invenio_records_resources.services.base.config import ServiceConfig
from invenio_records_resources.services.base.links import LinksTemplate
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from marshmallow import Schema, fields, post_load
from oarepo_runtime.services.results import RecordItem, RecordList

from oarepo_workflows.resolvers.auto_approve import AutoApproveEntity

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from flask_principal import Identity
    from invenio_records_resources.services.base.results import ServiceItemResult, ServiceListResult


class ArrayRecordItem(RecordItem):
    """Single record result for array-based records.

    Extends the base RecordItem to provide ID handling for array records.
    """

    @property
    def id(self) -> Any:  # TODO: what are possible options apart from str?
        """Get the record id."""
        return self._record["id"]


class ArrayRecordList(RecordList):
    """Result list for array-based records.

    Extends the base RecordItem to provide ID handling for array records.
    """

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

    @property
    @override
    def hits(self) -> Any:
        """Iterator over the hits."""
        for hit in self._results:
            # Project the record
            projection = self._schema.dump(
                hit,
                context={"identity": self._identity, "record": hit},
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(self._identity, hit)
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


class classproperty[T]:  # noqa N801
    # TODO: move to runtime
    """Class property decorator implementation.

    Allows defining properties at class level rather than instance level.
    Will be moved to runtime in future versions.
    """

    def __init__(self, func: Callable):
        """Initialize the class property."""
        self.fget = func

    def __get__(self, instance: Any, owner: Any) -> T:
        """Get the value of the class property."""
        return self.fget(owner)


def entity_schema_factory(keyword: str, entity: type) -> type:
    """Create a schema class for a given named entity."""

    @post_load
    def _make(self, **kwargs: Any) -> type:  # noqa ARG001, ANN001
        return entity(**kwargs)

    flds = {
        "keyword": fields.String(dump_only=True, dump_default=keyword),
        "id": fields.String(dump_only=True, dump_default="true"),
        "_make": _make,
    }
    return type(f"{keyword.capitalize()}Schema", (Schema,), flds)


class EntityService(Service):
    """Base abstract service class for entity operations.

    Provides core functionality for entity services including link templates
    and schema handling. Requires implementation of read operations.
    """

    @property
    def links_item_tpl(self) -> LinksTemplate:
        """Item links template."""
        return LinksTemplate(
            self.config.links_item,
        )

    @property
    def schema(self) -> ServiceSchemaWrapper:
        """Return the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    @abc.abstractmethod
    def read(self, identity: Identity, id_: str, **kwargs: Any) -> ServiceItemResult:
        """Return one instance."""
        raise NotImplementedError

    @abc.abstractmethod
    def read_many(
        self, identity: Identity, ids: Iterable[str], fields: Iterable[str] | None = None, **kwargs: Any
    ) -> ServiceListResult:
        """Return multiple instances."""
        raise NotImplementedError


class NamedEntityService(EntityService):
    """Service implementation for named entities.

    Provides concrete implementation of read operations for named entities
    that don't require database storage.
    """

    @override
    def read(self, identity: Identity, id_: str, **kwargs: Any) -> ServiceItemResult:
        result = self.config.entity_cls()
        return self.result_item(self, identity, record=result, links_tpl=self.links_item_tpl)

    @override
    def read_many(
        self, identity: Identity, ids: Iterable[str], fields: Iterable[str] | None = None, **kwargs: Any
    ) -> ServiceListResult:
        if not ids:
            return []
        results = [self.config.entity_cls() for _ in ids]
        return self.result_list(
            self,
            identity,
            results=results,
            links_item_tpl=self.links_item_tpl,
        )


class NamedEntityServiceConfig(ServiceConfig):
    """Base configuration for named entity services.

    Defines common configuration including result classes and schema generation
    capabilities for named entities.
    """

    links_item: ClassVar = {}
    result_item_cls = ArrayRecordItem
    result_list_cls = ArrayRecordList

    @classproperty
    def schema(cls) -> type[Schema]:  # noqa N805
        """Create the schema for the entity."""
        return entity_schema_factory(keyword=cls.keyword, entity=cls.entity_cls)


class AutoApproveEntityServiceConfig(NamedEntityServiceConfig):
    """Configuration for auto-approve entity service.

    Specific configuration for auto-approve workflow entities,
    defining service ID, keyword and entity class to use.
    """

    service_id = "auto_approve"
    keyword = "auto_approve"
    entity_cls = AutoApproveEntity
