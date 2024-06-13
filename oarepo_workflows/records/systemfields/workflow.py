from invenio_records.systemfields.base import SystemField

class WorkflowField(SystemField):
    def __init__(self, key="workflow", initial="default"):
        self._initial = initial
        super().__init__(key=key)

    def post_create(self, record):
        self.set_dictkey(record, self._initial)

    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self
        return self.get_dictkey(record)

    def __set__(self, record, value):
        self.set_dictkey(record, value)


"""
class WorkflowField(MappingSystemFieldMixin, SystemField):
    @property
    def mapping(self):
        return {
            self.attr_name: {
                "type": "keyword",
            },
        }

    def _get_workflow(self, record):
        if record.id is None:
            return
        try:
            res = (
                db.session.query(self._record_workflow_model.workflow)
                .filter(self._record_workflow_model.record_id == record.id)
                .one()
            )
            return res[0]
        except NoResultFound:
            return None

    def __init__(self, record_workflow_model, key="workflow"):
        self._workflow = None  # added in db
        self._record_workflow_model = record_workflow_model
        super().__init__(key=key)

    def pre_commit(self, record):
        super().pre_commit(record)
        try:
            comm_id = str(record.communities.default.id)
        except AttributeError:
            return
        workflow = self._get_workflow(record)
        if not workflow:
            try:
                res = (
                    db.session.query(CommunityWorkflowModel.workflow)
                    .filter(CommunityWorkflowModel.community_id == comm_id)
                    .one()
                )
                new = self._record_workflow_model(
                    workflow=res[0], record_id=str(record.id)
                )
                db.session.add(new)
            except NoResultFound:
                return

    def __get__(self, record, owner=None):
        if record is None:
            return self
        return self._get_workflow(record)
"""
