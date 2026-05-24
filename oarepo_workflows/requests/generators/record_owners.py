#
# Copyright (C) 2026 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""A record owners generator that enables the record owner to be a recipient of a request."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.generators import RecordOwners as BaseRecordOwners

from .recipient_generator import RecipientGeneratorMixin

if TYPE_CHECKING:
    from collections.abc import Mapping

    from invenio_records_resources.records import Record
    from invenio_requests.customizations import RequestType


class RecordOwnersForRecipients(RecipientGeneratorMixin, BaseRecordOwners):
    """A record owners generator that enables the record owner to be a recipient of a request."""

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:
        if not record:
            return []
        try:
            return [
                {
                    "user": str(record.parent.access.owner.resolve().id),  # type: ignore[reportAttributeAccessIssue]
                }
            ]
        except AttributeError:
            return []
