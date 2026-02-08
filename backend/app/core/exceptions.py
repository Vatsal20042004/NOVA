"""
Custom exception classes for the application
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(AppException):
    """Raised when user lacks required permissions"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)


class NotFoundError(AppException):
    """Raised when a resource is not found"""
    
    def __init__(self, resource: str = "Resource", resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=message, status_code=404)


class ValidationError(AppException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, details=details)


class ConflictError(AppException):
    """Raised when there's a conflict (e.g., duplicate email)"""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class InsufficientStockError(AppException):
    """Raised when inventory is insufficient"""
    
    def __init__(
        self,
        product_id: int,
        requested: int,
        available: int
    ):
        message = f"Insufficient stock for product {product_id}: requested {requested}, available {available}"
        super().__init__(
            message=message,
            status_code=400,
            details={
                "product_id": product_id,
                "requested": requested,
                "available": available
            }
        )


class PaymentError(AppException):
    """Raised when payment processing fails"""
    
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(message=message, status_code=402)


class RateLimitError(AppException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            details={"retry_after": retry_after}
        )


class DatabaseError(AppException):
    """Raised when database operation fails"""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message=message, status_code=500)


class LockAcquisitionError(AppException):
    """Raised when unable to acquire a lock"""
    
    def __init__(self, resource: str):
        message = f"Unable to acquire lock for {resource}"
        super().__init__(message=message, status_code=503)
