from invenio_records_resources.references.entity_resolvers import EntityProxy
from invenio_records_resources.references.entity_resolvers.base import EntityResolver
from flask_principal import Need


class AutoApprover:
    def __init__(self, value: bool):
        self.value = value


class AutoApproveProxy(EntityProxy):
    def _resolve(self) -> AutoApprover:
        value = self._parse_ref_dict_id()
        return AutoApprover(value)

    def get_needs(self, ctx=None) -> list[Need]:
        return []  # granttokens calls this

    def pick_resolved_fields(self, identity, resolved_dict) -> dict:
        return {"auto_approve": resolved_dict["id"]}


class AutoApproveResolver(EntityResolver):
    type_id = "auto_approve"

    def __init__(self):
        self.type_key = self.type_id
        super().__init__(
            "auto_approve",
        )

    def matches_reference_dict(self, ref_dict):
        return self._parse_ref_dict_type(ref_dict) == self.type_id

    def _reference_entity(self, entity):
        return {self.type_key: str(entity.value)}

    def matches_entity(self, entity):
        return isinstance(entity, AutoApprover)

    def _get_entity_proxy(self, ref_dict):
        return AutoApproveProxy(self, ref_dict)
