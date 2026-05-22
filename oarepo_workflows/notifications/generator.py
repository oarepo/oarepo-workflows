#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-workflows (see https://github.com/oarepo/oarepo-workflows).
#
# oarepo-workflows is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Action recipient generator for a notification."""

from __future__ import annotations

from typing import override

from invenio_access.models import ActionUsers
from invenio_db import db
from invenio_notifications.models import Notification, Recipient
from invenio_notifications.services.generators import (
    RecipientGenerator,
)
from invenio_records.dictutils import dict_lookup


class ActionRecipient(RecipientGenerator):
    """Role recipient generator for a notification."""

    def __init__(self, key: str):
        """Ctor."""
        self.key = key

    @override
    def __call__(self, notification: Notification, recipients: list[Recipient]):
        """Update required recipient information and add backend id."""
        action_need = dict_lookup(notification.context, self.key)
        action_name = action_need["id"]

        # look up users with this action need
        for au in db.session.query(ActionUsers).filter_by(action=action_name):
            user = au.user
            # TODO: should use service to get the representation
            recipients[user.id] = Recipient(data={"email": user.email})
        return recipients
