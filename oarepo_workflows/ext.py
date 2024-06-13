from functools import cached_property
import importlib_metadata

class OARepoWorkflows(object):

    def __init__(self, app=None):
        if app:
            self.init_app(app)
    @cached_property
    def state_changed_notifiers(self):
        group_name = 'oarepo_workflows.state_changed_notifiers'
        return importlib_metadata.entry_points().select(group=group_name)

    def set_state(self, record, value):
        previous_value = record.status
        record.status = value
        for state_changed_notifier in self.state_changed_notifiers:
            state_changed_notifier(record, previous_value, value)

    def init_app(self, app):
        """Flask application initialization."""
        self.app = app
        app.extensions["oarepo-workflows"] = self

