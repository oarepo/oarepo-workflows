# SPDX-FileCopyrightText: 2024 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Auto request and auto approve generators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Never, override

from invenio_access import SystemRoleNeed
from invenio_records_permissions.generators import Generator

from ...resolvers.auto_approve import AutoApprove as AutoApproveEntity
from .recipient_generator import RecipientGeneratorMixin

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from flask_principal import Need
    from invenio_records_resources.records import Record
    from invenio_requests.customizations import RequestType

auto_request_need = SystemRoleNeed("auto_request")
auto_approve_need = SystemRoleNeed("auto_approve")


class AutoApprove(RecipientGeneratorMixin, Generator):
    """Auto approve generator.

    If the generator is used within recipients of a request,
    the request will be automatically approved when the request is submitted.
    """

    @override
    def reference_receivers(
        self,
        record: Record | None = None,
        request_type: RequestType | None = None,
        **kwargs: Any,
    ) -> list[Mapping[str, str]]:
        """Return the reference receiver(s) of the auto-approve request.

        Returning "auto_approve" is a signal to the workflow that the request should be auto-approved.
        """
        return [AutoApproveEntity.ref_dict]

    @override
    def needs(self, **context: Any) -> Sequence[Need]:
        """Get needs that signal workflow to automatically approve the request."""
        raise ValueError(
            "Auto-approve generator can not create needs and "
            "should be used only in `recipient` section of WorkflowRequest."
        )

    @override
    def excludes(self, **context: Any) -> Sequence[Need]:
        """Get needs that signal workflow to automatically approve the request."""
        raise ValueError(
            "Auto-approve generator can not create needs and "
            "should be used only in `recipient` section of WorkflowRequest."
        )

    @override
    def query_filter(self, **context: Any) -> Never:
        """Get needs that signal workflow to automatically approve the request."""
        raise ValueError(
            "Auto-approve generator can not create needs and "
            "should be used only in `recipient` section of WorkflowRequest."
        )
