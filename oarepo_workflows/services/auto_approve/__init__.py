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
from collections.abc import Iterable
from typing import Any, Callable

from invenio_records_resources.services.base.config import ServiceConfig
from invenio_records_resources.services.base.links import LinksTemplate
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper
from marshmallow import Schema, fields
from oarepo_runtime.services.results import RecordItem, RecordList
from marshmallow import post_load
from oarepo_workflows.resolvers.auto_approve import AutoApproveEntity

class ArrayRecordItem(RecordItem):
    """Single record result."""

    @property
    def id(self):
        """Get the record id."""
        return self._record["id"]


class ArrayRecordList(RecordList):
    # move to runtime

    @property
    def total(self):
        """Get total number of hits."""
        return len(self._results)

    @property
    def aggregations(self):
        """Get the search result aggregations."""
        return None

    @property
    def hits(self):
        """Iterator over the hits."""
        for hit in self._results:
            # Project the record
            projection = self._schema.dump(
                hit,
                context=dict(
                    identity=self._identity,
                    record=hit,
                ),
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

class classproperty[T]: #TODO: move to runtime
    """move to runtime"""

    def __init__(self, func: Callable):
        """Initialize the class property."""
        self.fget = func

    def __get__(self, instance: Any, owner: Any) -> T:
        """Get the value of the class property."""
        return self.fget(owner)

def entity_schema_factory(keyword: str, entity: type)->type[Schema]:
    @post_load
    def _make(self, **kwargs):
        return entity(**kwargs)

    flds = {"keyword": fields.String(dump_only=True, dump_default=keyword),
            "id": fields.String(dump_only=True, dump_default="true"),
            "_make": _make}
    MySchema = type(f"{keyword.capitalize()}Schema", (Schema,), flds)
    return MySchema

class EntityService(Service):
    @property
    def links_item_tpl(self):
        """Item links template."""
        return LinksTemplate(
            self.config.links_item,
        )

    @property
    def schema(self):
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    @abc.abstractmethod
    def read(self, identity, id_, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def read_many(self, identity, ids: Iterable[str], fields=None, **kwargs):
        raise NotImplementedError


class NamedEntityService(EntityService):

    def read(self, identity, id_, **kwargs):
        result = self.config.entity_cls()
        return self.result_item(self, identity, record=result, links_tpl=self.links_item_tpl)

    def read_many(self, identity, ids: Iterable[str], fields=None, **kwargs):
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
    links_item = {}
    result_item_cls = ArrayRecordItem
    result_list_cls = ArrayRecordList

    @classproperty
    def schema(cls):
        return entity_schema_factory(keyword=cls.keyword, entity=cls.entity_cls)


class AutoApproveEntityServiceConfig(NamedEntityServiceConfig):
    """Configuration for auto-approve entity service."""

    service_id = "auto_approve"
    keyword = "auto_approve"
    entity_cls = AutoApproveEntity

