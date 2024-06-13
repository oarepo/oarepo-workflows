class WorkflowRequest:
    def __init__(self, requesters, recipients, transitions):
        self.requesters = requesters
        self.recipients = recipients
        self.transitions = transitions

class WorkflowTransitions:
    def __init__(self, submit, approve, decline):
        self.submit = submit
        self.approve = approve
        self.decline = decline