#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Service for reading multiple-recipients entities."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, override

import marshmallow as ma
from oarepo_runtime.services.entity.config import EntityServiceConfig
from oarepo_runtime.services.entity.service import EntityService

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flask_principal import Identity
    from invenio_records_resources.services.records.results import (
        RecordItem,
        RecordList,
    )


class MultipleEntitiesEntitySchema(ma.Schema):
    """Schema for multiple recipients entities."""

    entities = ma.fields.List(
        ma.fields.Dict(keys=ma.fields.String(), values=ma.fields.String())
    )


class MultipleEntitiesEntityServiceConfig(EntityServiceConfig):
    """Configuration for auto-approve entity service."""

    service_id = "multiple"
    schema = MultipleEntitiesEntitySchema


class MultipleEntitiesEntityService(EntityService):
    """Service for reading auto-approve entities."""

    @override
    def read(self, identity: Identity, id_: str, **kwargs: Any) -> RecordItem:
        return self.result_item(
            self,
            identity,
            record={"entities": json.loads(id_)},
            links_tpl=self.links_item_tpl,
        )

    @override
    def read_many(
        self,
        identity: Identity,
        ids: Iterable[str],
        fields: list[str] | None = None,
        **kwargs: Any,
    ) -> RecordList:
        results = []
        if ids:
            results = [{"entities": json.loads(id_)} for id_ in ids]
        return self.result_list(
            self,
            identity,
            results=results,
            links_item_tpl=self.links_item_tpl,
        )
