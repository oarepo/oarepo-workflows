#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""App blueprints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, Flask

if TYPE_CHECKING:
    from flask.blueprints import BlueprintSetupState


def create_app_blueprint(app: Flask) -> Blueprint:
    """Create requests blueprint."""
    blueprint = Blueprint("oarepo-workflows", __name__)

    # noinspection PyUnusedLocal
    def register_auto_approve_entity_resolver(state: BlueprintSetupState) -> None:
        from oarepo_workflows.resolvers.auto_approve import AutoApproveResolver

        requests = app.extensions["invenio-requests"]
        requests.entity_resolvers_registry.register_type(AutoApproveResolver())

    blueprint.record_once(register_auto_approve_entity_resolver)

    return blueprint
