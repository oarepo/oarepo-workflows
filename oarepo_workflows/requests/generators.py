#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Need generators."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, Optional

from invenio_access import SystemRoleNeed
from invenio_records_permissions.generators import Generator

if TYPE_CHECKING:
    from flask_principal import Need
    from invenio_records_resources.records import Record
    from invenio_requests.customizations.request_types import RequestType


@dataclasses.dataclass
class MultipleGeneratorsGenerator(Generator):
    """A generator that combines multiple generators with 'or' operation."""

    generators: list[Generator] | tuple[Generator]
    """List of generators to be combined."""

    def needs(self, **context: Any) -> set[Need]:
        """Generate a set of needs from generators that a person needs to have.

        :param context: Context.
        :return: Set of needs.
        """
        return {
            need for generator in self.generators for need in generator.needs(**context)
        }

    def excludes(self, **context: Any) -> set[Need]:
        """Generate a set of needs that person must not have.

        :param context: Context.
        :return: Set of needs.
        """
        return {
            exclude
            for generator in self.generators
            for exclude in generator.excludes(**context)
        }

    def query_filters(self, **context: Any) -> list[dict]:
        """Generate a list of opensearch query filters.

         These filters are used to filter objects. These objects are governed by a policy
         containing this generator.

        :param context: Context.
        """
        return [
            query_filter
            for generator in self.generators
            for query_filter in generator.query_filter(**context)
        ]


auto_request_need = SystemRoleNeed("auto_request")
auto_approve_need = SystemRoleNeed("auto_approve")


class AutoRequest(Generator):
    """Auto request generator.

    This generator is used to automatically create a request
    when a record is moved to a specific state.
    """

    def needs(self, **context: Any) -> list[Need]:
        """Get needs that signal workflow to automatically create the request."""
        return [auto_request_need]


class RecipientGeneratorMixin:
    """Mixin for permission generators that can be used as recipients in WorkflowRequest."""

    def reference_receivers(
        self,
        record: Optional[Record] = None,
        request_type: Optional[RequestType] = None,
        **context: Any,
    ) -> list[dict[str, str]]:
        """Return the reference receiver(s) of the request.

        This call requires the context to contain at least "record" and "request_type"

        Must return a list of dictionary serialization of the receivers.

        Might return empty list or None to indicate that the generator does not
        provide any receivers.
        """
        raise NotImplementedError("Implement reference receiver in your code")


class AutoApprove(RecipientGeneratorMixin, Generator):
    """Auto approve generator.

    If the generator is used within recipients of a request,
    the request will be automatically approved when the request is submitted.
    """

    def reference_receivers(
        self,
        record: Optional[Record] = None,
        request_type: Optional[RequestType] = None,
        **kwargs: Any,
    ) -> list[dict[str, str]]:
        """Return the reference receiver(s) of the auto-approve request.

        Returning "auto_approve" is a signal to the workflow that the request should be auto-approved.
        """
        return [{"auto_approve": "true"}]
