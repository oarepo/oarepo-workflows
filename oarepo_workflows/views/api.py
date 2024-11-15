from __future__ import annotations

from flask import Blueprint
from flask.blueprints import Blueprint


def create_api_blueprint(app) -> Blueprint:
    """Create requests blueprint."""
    blueprint = Blueprint("oarepo-workflows", __name__)

    def register_autoapprove_entity_resolver(state) -> None:
        from oarepo_workflows.resolvers.auto_approve import AutoApproveResolver
        requests = app.extensions["invenio-requests"]
        requests.entity_resolvers_registry.register_type(AutoApproveResolver())

    blueprint.record_once(register_autoapprove_entity_resolver)

    return blueprint
