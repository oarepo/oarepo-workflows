# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Proxies for accessing the current OARepo workflows extension without bringing dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from oarepo_workflows.ext import OARepoWorkflows

current_oarepo_workflows: OARepoWorkflows = LocalProxy(lambda: current_app.extensions["oarepo-workflows"])  # type: ignore[assignment]
"""Proxy to access the current OARepo workflows extension."""
