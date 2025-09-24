#
# Copyright (C) 2025 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Default configuration for oarepo-workflows to be initialized at invenio_config.module entrypoint."""

from __future__ import annotations

from oarepo_workflows.requests.permissions import (
    CreatorsFromWorkflowRequestsPermissionPolicy,
)

REQUESTS_PERMISSION_POLICY = CreatorsFromWorkflowRequestsPermissionPolicy
