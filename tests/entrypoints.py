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

from invenio_records_resources.references.entity_resolvers.records import RecordProxy, RecordResolver

if TYPE_CHECKING:
    from typing import Any

state_change_notifier_called = False
workflow_change_notifier_called = False

# TODO: this would be easier to move to oarepo-requests
class MockDraftResolver(RecordResolver):
    """Resolver for records."""

    def __init__(self, record_cls, service_id, type_key="record", proxy_cls=RecordProxy):
        """Constructor.

        :param record_cls: The record class to use.
        :param service_id: The record service id.
        :param type_key: The value to use for the TYPE part of the ref_dicts.
        """
        self.record_cls = record_cls
        self.type_key = type_key
        self.proxy_cls = proxy_cls
        super().__init__(service_id)

    def matches_entity(self, entity):
        """Check if the entity is a record."""
        return isinstance(entity, self.record_cls)

    def _reference_entity(self, entity):
        """Create a reference dict for the given record."""
        return {self.type_key: str(entity.pid.pid_value)}

    def matches_reference_dict(self, ref_dict):
        """Check if the reference dict references a request."""
        return self._parse_ref_dict_type(ref_dict) == self.type_key

    def _get_entity_proxy(self, ref_dict):
        """Return a RecordProxy for the given reference dict."""
        return self.proxy_cls(self, ref_dict, self.record_cls)


def state_change_notifier_called_marker(*args: Any, **_kwargs: Any):
    global state_change_notifier_called  # noqa PLW0603
    state_change_notifier_called = True

# TODO: scrap
def workflow_change_notifier_called_marker(*args: Any, **_kwargs: Any):
    global workflow_change_notifier_called  # noqa PLW0603
    workflow_change_notifier_called = True
