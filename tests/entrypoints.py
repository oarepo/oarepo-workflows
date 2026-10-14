# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

state_change_notifier_called = False
workflow_change_notifier_called = False


def state_change_notifier_called_marker(*args: Any, **_kwargs: Any):
    global state_change_notifier_called  # noqa PLW0603
    state_change_notifier_called = True
