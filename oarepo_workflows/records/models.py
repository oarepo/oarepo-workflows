from __future__ import annotations

from invenio_db import db
from sqlalchemy import String


class RecordWorkflowParentModelMixin:
    workflow = db.Column(String)
