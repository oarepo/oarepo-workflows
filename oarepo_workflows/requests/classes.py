class WorkflowRequest:
    def __init__(self, requesters, recipients, transitions):
        self.requesters = requesters
        self.recipients = recipients
        self.transitions = transitions


class WorkflowTransitions:
    def __init__(self, submitted=None, approved=None, declined=None):
        self.submitted = submitted
        self.approved = approved
        self.declined = declined
