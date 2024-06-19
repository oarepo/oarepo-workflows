from invenio_records.systemfields.base import SystemField


class WorkflowField(SystemField):
    def __init__(self, key="workflow", default="default"):
        self._default = default
        super().__init__(key=key)

    def post_create(self, record):
        self.set_dictkey(record, self._default)

    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self
        return self.get_dictkey(record)

    def __set__(self, record, value):
        self.set_dictkey(record, value)
