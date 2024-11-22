#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from oarepo_workflows.requests import AutoRequest
from oarepo_workflows.requests.generators.auto import auto_request_need


def test_auto_request_needs(app):
    assert AutoRequest().needs() == [auto_request_need]
