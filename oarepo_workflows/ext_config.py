#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Default configuration for oarepo-workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oarepo_workflows.notifications.generator import ActionRecipient

if TYPE_CHECKING:
    from oarepo_workflows import Workflow

"""Permissions presets for oarepo-workflows."""

WORKFLOWS: dict[str, Workflow] = {}
"""Configuration of workflows, must be provided by the user inside, for example, invenio.cfg."""

WORKFLOWS_ALLOWED_REQUEST_RECEIVERS = ["multiple", "action_need"]

WORKFLOWS_DEFAULT_WORKFLOW = "individual"

NOTIFICATION_RECIPIENTS_RESOLVERS = {
    "action_need": lambda key, notification: ActionRecipient(key),  # noqa ARG005
}
