# app/core/exceptions.py


class AppError(Exception):
    """Base para todas as exceções de domínio."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    pass


class ConflictError(AppError):
    pass


class ForbiddenError(AppError):
    pass


class BusinessRuleError(AppError):
    pass


class UnauthorizedError(AppError):
    pass