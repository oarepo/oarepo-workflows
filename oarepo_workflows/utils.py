def get_workflow_from_record(record, **kwargs):
    if hasattr(record, "parent"):
        record = record.parent
    if hasattr(record, "workflow") and record.workflow:
        return record.workflow
    else:
        return None
