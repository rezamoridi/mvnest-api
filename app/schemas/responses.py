
from fastapi import status
from pydantic import BaseModel, Field
from typing import Dict, Any

class DetailResponse(BaseModel):
    """A consistent schema for detailed success messages."""
    sub: int
    username: str
    email: str

class SuccessResponse(BaseModel):
    """A generic success response structure."""
    message: str = Field(..., example="User created successfully")
    detail: DetailResponse

class ErrorResponse(BaseModel):
    """A generic error response structure."""
    detail: str

# Define a dictionary for common error responses with specific examples
COMMON_ERROR_RESPONSES = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "Duplicated data such as user-email or username already exists.",
        "content": {
            "application/json": {
                "example": {"detail": "Username 'johndoe' already exists."}
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "Access denied to this endpoint.",
        "content": {
            "application/json": {
                "example": {"detail": "Not enough permissions to access this resource."}
            }
        },
    },
}