# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Proxies for accessing the current OARepo workflows extension without bringing dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import current_app
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from oarepo_workflows.ext import OARepoWorkflows

current_oarepo_workflows: OARepoWorkflows = cast(
    "OARepoWorkflows", LocalProxy(lambda: current_app.extensions["oarepo-workflows"])
)
"""Proxy to access the current OARepo workflows extension."""
