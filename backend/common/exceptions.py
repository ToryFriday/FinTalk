"""
Custom exception classes for the FinTalk application.
"""


class PostNotFoundError(Exception):
    """Raised when a post is not found."""
    def __init__(self, post_id):
        self.post_id = post_id
        super().__init__(f"Post with id {post_id} not found")


class ValidationError(Exception):
    """Raised when data validation fails."""
    def __init__(self, message, errors=None):
        self.errors = errors or {}
        super().__init__(message)


class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass