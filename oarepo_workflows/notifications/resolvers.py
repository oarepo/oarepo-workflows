#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see https://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Notification resolvers for action needs."""

from __future__ import annotations

from invenio_records_resources.references.entity_resolvers import (
    ServiceResultResolver,
)


def action_resolver() -> ServiceResultResolver:
    """Return action need notification resolver."""
    return ServiceResultResolver(service_id="action_need", type_key="action_need")


action_resolver.type_key = "action_need"  # type: ignore[reportFunctionMemberAccess, attr-defined]
