#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see http://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

_state_change_notifier_called = False
_workflow_change_notifier_called = False

def state_change_notifier_called_marker(*args: Any, **_kwargs: Any):
    global _state_change_notifier_called
    _state_change_notifier_called = True

def workflow_change_notifier_called_marker(*args: Any, **_kwargs: Any):
    global _workflow_change_notifier_called
    _workflow_change_notifier_called = True