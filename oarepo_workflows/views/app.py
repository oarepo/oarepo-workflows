from flask import Blueprint

def create_app_blueprint(app):
    """Create requests blueprint."""
    blueprint = Blueprint("oarepo-workflows", __name__)

    def register_autoapprove_entity_resolver(state) -> None:
        from oarepo_workflows.resolvers.auto_approve import AutoApproveResolver
        requests = app.extensions["invenio-requests"]
        requests.entity_resolvers_registry.register_type(AutoApproveResolver())

    blueprint.record_once(register_autoapprove_entity_resolver)

    return blueprint
