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

from oarepo_runtime.services.entity.config import KeywordEntityServiceConfig
from oarepo_runtime.services.entity.service import KeywordEntityService


class AutoApproveEntityServiceConfig(KeywordEntityServiceConfig):
    """Configuration for auto-approve entity service."""

    service_id = "auto_approve"
    keyword = "auto_approve"


class AutoApproveEntityService(KeywordEntityService):
    """Service for reading auto-approve entities."""

    pass
