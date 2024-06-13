from invenio_records_permissions.generators import ConditionalGenerator

class IfInState(ConditionalGenerator):
    def __init__(self, state, then_):
        super().__init__(then_, else_=[])
        self.state = state

    def _condition(self, record, **kwargs):
        try:
            state = record.status
        except AttributeError:
            return False
        return state == self.state