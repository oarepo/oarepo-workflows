from oarepo_workflows import AutoRequest
from oarepo_workflows.requests.generators import auto_request_need


def test_auto_request_needs(app):
    assert AutoRequest().needs() == [auto_request_need]