#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Mixin for permission generators that can be used as recipients in WorkflowRequest."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from invenio_records_resources.records import Record
    from invenio_requests.customizations import RequestType


class RecipientGeneratorMixin:
    """Mixin for permission generators that can be used as recipients in WorkflowRequest."""

    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **context: Any,
    ) -> list[Mapping[str, str]]:  # pragma: no cover
        """Return the reference receiver(s) of the request.

        This call requires the context to contain at least "record" and "request_type"

        Must return a list of dictionary serialization of the receivers.

        Might return empty list or None to indicate that the generator does not
        provide any receivers.
        """
        raise NotImplementedError("Implement reference receiver in your code")
