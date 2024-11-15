#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Default configuration for oarepo-workflows."""

from __future__ import annotations

from oarepo_workflows.services.permissions.record_permission_policy import (
    WorkflowRecordPermissionPolicy,
)

OAREPO_PERMISSIONS_PRESETS = {
    "workflow": WorkflowRecordPermissionPolicy,
}
"""Permissions presets for oarepo-workflows."""

WORKFLOWS = {}
"""Configuration of workflows, must be provided by the user inside, for example, invenio.cfg."""
