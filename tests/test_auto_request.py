# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from oarepo_workflows.requests import AutoRequest
from oarepo_workflows.requests.generators.auto import auto_request_need


def test_auto_request_needs(app, search_clear):
    assert AutoRequest().needs() == [auto_request_need]
