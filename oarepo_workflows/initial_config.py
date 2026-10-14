# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Default configuration for oarepo-workflows to be initialized at invenio_config.module entrypoint."""

from __future__ import annotations

from oarepo_workflows.requests.permissions import (
    CreatorsFromWorkflowRequestsPermissionPolicy,
)

REQUESTS_PERMISSION_POLICY = CreatorsFromWorkflowRequestsPermissionPolicy
