#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

from flask import Blueprint
from flask.blueprints import Blueprint


def create_app_blueprint(app) -> Blueprint:
    """Create requests blueprint."""
    blueprint = Blueprint("oarepo-workflows", __name__)

    def register_autoapprove_entity_resolver(state) -> None:
        from oarepo_workflows.resolvers.auto_approve import AutoApproveResolver

        requests = app.extensions["invenio-requests"]
        requests.entity_resolvers_registry.register_type(AutoApproveResolver())

    blueprint.record_once(register_autoapprove_entity_resolver)

    return blueprint
