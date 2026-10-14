# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Notification resolvers for action needs."""

from __future__ import annotations

from invenio_records_resources.references.entity_resolvers import (
    ServiceResultResolver,
)


# TODO: consider moving to requests
def action_resolver() -> ServiceResultResolver:
    """Return action need notification resolver."""
    return ServiceResultResolver(service_id="action_need", type_key="action_need")


action_resolver.type_key = "action_need"  # ty: ignore[unresolved-attribute]
