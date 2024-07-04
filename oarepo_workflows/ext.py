from functools import cached_property

import importlib_metadata


class OARepoWorkflows(object):

    def __init__(self, app=None):
        if app:
            self.init_config(app)
            self.init_app(app)

    def init_config(self, app):
        """Initialize configuration."""
        from . import ext_config

        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}

        for k in ext_config.OAREPO_PERMISSIONS_PRESETS:
            if k not in app.config["OAREPO_PERMISSIONS_PRESETS"]:
                app.config["OAREPO_PERMISSIONS_PRESETS"][k] = (
                    ext_config.OAREPO_PERMISSIONS_PRESETS[k]
                )

    @cached_property
    def state_changed_notifiers(self):
        group_name = "oarepo_workflows.state_changed_notifiers"
        return importlib_metadata.entry_points().select(group=group_name)

    @cached_property
    def workflow_changed_notifiers(self):
        group_name = "oarepo_workflows.workflow_changed_notifiers"
        return importlib_metadata.entry_points().select(group=group_name)

    @cached_property
    def default_workflow_getters(self):
        group_name = "oarepo_workflows.default_workflow_getters"
        return importlib_metadata.entry_points().select(group=group_name)

    def set_state(self, identity, record, value, *args, uow=None, **kwargs):
        previous_value = record.state
        record.state = value
        for state_changed_notifier_ep in self.state_changed_notifiers:
            state_changed_notifier = state_changed_notifier_ep.load()
            state_changed_notifier(
                identity, record, previous_value, value, *args, uow=uow, **kwargs
            )

    def get_default_workflow(self, default="default", *args, **kwargs):
        for default_workflow_getter_ep in self.default_workflow_getters:
            default_workflow_getter = default_workflow_getter_ep.load()
            default = default_workflow_getter(default, *args, **kwargs)
        return default

    def set_workflow(self, identity, record, value, *args, uow=None, **kwargs):
        previous_value = record.parent["workflow"]
        record.parent.workflow = value
        for workflow_changed_notifier_ep in self.workflow_changed_notifiers:
            workflow_changed_notifier = workflow_changed_notifier_ep.load()
            workflow_changed_notifier(
                identity, record, previous_value, value, *args, uow=uow, **kwargs
            )

    @property
    def record_workflows(self):
        return self.app.config["RECORD_WORKFLOWS"]

    def init_app(self, app):
        """Flask application initialization."""
        self.app = app
        app.extensions["oarepo-workflows"] = self
