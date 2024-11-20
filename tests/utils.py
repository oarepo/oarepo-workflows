def test_state_change_notifier(*args, **_kwargs):
    record = args[1]
    record["state-change-notifier-called"] = True


def test_workflow_change_notifier(*args, **_kwargs):
    record = args[1]
    record.parent["workflow-change-notifier-called"] = True
