"""
Error Handling and Response Models - Standardized error responses across all APIs.

Ensures all endpoints return consistent error format for frontend consumption.
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for frontend error handling."""
    # Configuration errors
    LLM_NOT_CONFIGURED = "LLM_NOT_CONFIGURED"
    INVALID_LLM_URL = "INVALID_LLM_URL"
    LLM_CONNECTION_FAILED = "LLM_CONNECTION_FAILED"
    NO_MODELS_AVAILABLE = "NO_MODELS_AVAILABLE"
    INVALID_MODEL = "INVALID_MODEL"
    
    # Routing errors
    INVALID_ROUTING_PROFILE = "INVALID_ROUTING_PROFILE"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    
    # Conversation/Message errors
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    MESSAGE_NOT_FOUND = "MESSAGE_NOT_FOUND"
    INVALID_CONVERSATION_ID = "INVALID_CONVERSATION_ID"
    
    # Request errors
    INVALID_REQUEST = "INVALID_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # Timeout errors
    REQUEST_TIMEOUT = "REQUEST_TIMEOUT"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    
    # Server errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    success: bool = Field(default=False, description="Always False for error responses")
    error_code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="User-friendly error message")
    detail: Optional[str] = Field(None, description="Additional technical details")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    suggestions: Optional[list[str]] = Field(None, description="Suggested actions to resolve error")


class SuccessResponse(BaseModel):
    """Standardized success response model."""
    success: bool = Field(default=True, description="Always True for success responses")
    data: Any = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Optional success message")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


def create_error_response(
    error_code: ErrorCode,
    message: str,
    detail: Optional[str] = None,
    suggestions: Optional[list[str]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """
    Create a standardized error response.
    
    Args:
        error_code: Machine-readable error code
        message: User-friendly error message
        detail: Optional technical details
        suggestions: Optional list of suggested actions
        request_id: Optional request tracking ID
        
    Returns:
        Standardized ErrorResponse
    """
    return ErrorResponse(
        success=False,
        error_code=error_code,
        message=message,
        detail=detail,
        suggestions=suggestions,
        request_id=request_id
    )


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> SuccessResponse:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Optional success message
        request_id: Optional request tracking ID
        
    Returns:
        Standardized SuccessResponse
    """
    return SuccessResponse(
        success=True,
        data=data,
        message=message,
        request_id=request_id
    )


def handle_llm_not_configured_error(request_id: Optional[str] = None) -> ErrorResponse:
    """LLM server not configured error."""
    return create_error_response(
        error_code=ErrorCode.LLM_NOT_CONFIGURED,
        message="LLM server is not configured",
        detail="No LLM_BASE_URL environment variable set",
        suggestions=[
            "Navigate to Settings > LLM Configuration",
            "Enter your LLM server URL (e.g., http://10.99.70.200:4000)",
            "Click 'Test & Save'",
            "Return to Chat Studio"
        ],
        request_id=request_id
    )


def handle_llm_connection_error(url: str, reason: str, request_id: Optional[str] = None) -> ErrorResponse:
    """LLM server connection error."""
    return create_error_response(
        error_code=ErrorCode.LLM_CONNECTION_FAILED,
        message=f"Cannot connect to LLM server at {url}",
        detail=reason,
        suggestions=[
            "Verify LLM server is running",
            "Check if URL is correct: http://host:port (no paths like /api/chat)",
            "Try using fallback ports: 9000, 4000, 8000, 3000",
            "Check firewall and network connectivity",
            "If using remote server, ensure it's accessible from this machine"
        ],
        request_id=request_id
    )


def handle_invalid_routing_profile_error(profile: str, valid_profiles: list[str], request_id: Optional[str] = None) -> ErrorResponse:
    """Invalid routing profile error."""
    return create_error_response(
        error_code=ErrorCode.INVALID_ROUTING_PROFILE,
        message=f"Routing profile '{profile}' is not valid",
        detail=f"Valid profiles: {', '.join(valid_profiles)}",
        suggestions=[
            "Reload routing profiles from server",
            "Select from available profiles only",
            "Contact administrator if custom profile is needed"
        ],
        request_id=request_id
    )


def handle_model_not_found_error(model_id: str, request_id: Optional[str] = None) -> ErrorResponse:
    """Model not found error."""
    return create_error_response(
        error_code=ErrorCode.INVALID_MODEL,
        message=f"Model '{model_id}' not found",
        detail="Model may have been removed or server configuration changed",
        suggestions=[
            "Reload model list from server",
            "Select a different available model",
            "Check LLM server configuration"
        ],
        request_id=request_id
    )


def handle_conversation_not_found_error(conversation_id: str, request_id: Optional[str] = None) -> ErrorResponse:
    """Conversation not found error."""
    return create_error_response(
        error_code=ErrorCode.CONVERSATION_NOT_FOUND,
        message=f"Conversation '{conversation_id}' not found",
        detail="Conversation may have been deleted",
        suggestions=[
            "Create a new conversation",
            "Reload conversation list",
            "Check if conversation ID is correct"
        ],
        request_id=request_id
    )


def handle_timeout_error(operation: str, timeout_seconds: int, request_id: Optional[str] = None) -> ErrorResponse:
    """Request timeout error."""
    return create_error_response(
        error_code=ErrorCode.REQUEST_TIMEOUT,
        message=f"{operation} timed out after {timeout_seconds} seconds",
        detail="Operation took longer than expected to complete",
        suggestions=[
            "Check if LLM server is responsive",
            "Try sending a shorter message",
            "Verify network connectivity",
            "If using slow remote server, contact administrator to increase timeout",
            "Retry the operation"
        ],
        request_id=request_id
    )


def handle_validation_error(field: str, issue: str, request_id: Optional[str] = None) -> ErrorResponse:
    """Request validation error."""
    return create_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=f"Validation failed: {field}",
        detail=issue,
        suggestions=[
            "Check the provided value is in correct format",
            "Ensure all required fields are provided",
            "Review API documentation for field requirements"
        ],
        request_id=request_id
    )


def handle_internal_server_error(operation: str, error_message: str, request_id: Optional[str] = None) -> ErrorResponse:
    """Internal server error."""
    logger.error(f"[{request_id}] Internal server error during {operation}: {error_message}")
    return create_error_response(
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        message=f"Internal server error occurred during {operation}",
        detail=error_message if logger.level == logging.DEBUG else None,
        suggestions=[
            "Check server logs for more details",
            "Try again in a few moments",
            "Contact administrator if problem persists"
        ],
        request_id=request_id
    )


# HTTP Exception mappings
class HTTPExceptionWithErrorCode(HTTPException):
    """HTTPException with standardized error code."""
    
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        detail: Optional[str] = None,
        suggestions: Optional[list[str]] = None,
        request_id: Optional[str] = None
    ):
        self.error_response = create_error_response(
            error_code=error_code,
            message=message,
            detail=detail,
            suggestions=suggestions,
            request_id=request_id
        )
        super().__init__(
            status_code=status_code,
            detail=self.error_response.dict()
        )
