from marshmallow import ValidationError


class MissingWorkflowError(ValidationError):
    """
    Exception raised when a required workflow is missing.
    Attributes:
        message -- explanation of the error
    """
    


class InvalidWorkflowError(ValidationError):
    """
    Exception raised when a workflow is invalid.
    Attributes:
        message -- explanation of the error
    """

