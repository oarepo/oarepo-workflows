import dataclasses
from typing import List, Tuple

from flask_principal import Need
from invenio_records_permissions.generators import Generator


@dataclasses.dataclass
class WorkflowEvent:
    submitters: List[Generator] | Tuple[Generator]

    def needs(self, **kwargs) -> set[Need]:
        return {
            need for generator in self.submitters for need in generator.needs(**kwargs)
        }

    def excludes(self, **kwargs) -> set[Need]:
        return {
            exclude
            for generator in self.submitters
            for exclude in generator.excludes(**kwargs)
        }

    def query_filters(self, **kwargs) -> list[dict]:
        return [
            query_filter
            for generator in self.submitters
            for query_filter in generator.query_filter(**kwargs)
        ]
