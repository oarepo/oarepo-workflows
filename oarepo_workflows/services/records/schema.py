import marshmallow as ma
from invenio_drafts_resources.services.records.schema import ParentSchema


class WorkflowParentSchema(ParentSchema):
    workflow = ma.fields.String()
