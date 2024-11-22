#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Proxies for accessing the current OARepo workflows extension without bringing dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from oarepo_workflows.ext import OARepoWorkflows

current_oarepo_workflows: OARepoWorkflows = LocalProxy(  # type: ignore
    lambda: current_app.extensions["oarepo-workflows"]
)
"""Proxy to access the current OARepo workflows extension."""
