import dataclasses
from typing import List, Tuple

from invenio_records_permissions.generators import Generator


@dataclasses.dataclass
class WorkflowEvent:
    submitters: List[Generator] | Tuple[Generator]

    def needs(self, **kwargs):
        return {
            need for generator in self.submitters for need in generator.needs(**kwargs)
        }

    def excludes(self, **kwargs):
        return {
            exclude
            for generator in self.submitters
            for exclude in generator.excludes(**kwargs)
        }

    def query_filters(self, **kwargs):
        return [
            query_filter
            for generator in self.submitters
            for query_filter in generator.query_filter(**kwargs)
        ]
