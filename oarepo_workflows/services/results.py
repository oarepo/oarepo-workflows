from collections.abc import Sequence
from typing import Any


# TODO: this is used as AttrList in opensearch-dsl; idk whether its allowed to use here (ie. dependence of different search backend)
class FakeHits:
    def __init__(self, hits: Sequence[Any]):
        self.hits = hits
        self.total = {"value": len(hits)}

    def __iter__(self):
        return iter(self.hits)


class FakeResults:
    def __init__(self, hits):
        self.hits = hits
        self.labelled_facets = []

    def __iter__(self):
        return iter(self.hits)

    def __len__(self):
        return len(self.hits.hits)


from invenio_records_resources.services.records.results import RecordList


class InMemoryResultList(RecordList):
    def __init__(
        self,
        service,
        identity,
        results,
        params=None,
        links_tpl=None,
        links_item_tpl=None,
        nested_links_item=None,
        schema=None,
        expandable_fields=None,
        expand=False,
    ):
        """Constructor.

        :params service: a service instance
        :params identity: an identity that performed the service request
        :params results: the search results
        :params params: dictionary of the query parameters
        """
        hits = FakeHits(results)
        results = FakeResults(hits)
        super().__init__(
            service,
            identity,
            results,
            params,
            links_tpl,
            links_item_tpl,
            nested_links_item,
            schema,
            expandable_fields,
            expand,
        )

    @property
    def hits(self):
        """Iterator over the hits."""
        for record in self._results:  # here we can just use the instantiated entity objects
            # Load dump
            # TODO: the line below i think does stuff that doesn't make sense if we don't have real search results
            # record = self._service.record_cls.loads(hit.to_dict()) # this is completely unnecessary imo?

            # Project the record
            projection = self._schema.dump(
                record,
                context={
                    "identity": self._identity,
                    "record": record,
                },
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(self._identity, record)
            if self._nested_links_item:
                for link in self._nested_links_item:
                    link.expand(self._identity, record, projection)

            yield projection
