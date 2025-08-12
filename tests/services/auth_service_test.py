import pytest
import jwt
from datetime import timedelta

from fastapi import HTTPException

# Auth middeware function for test
from app.schemas import schemas
from app.middleware.auth_middleware import (
    create_access_token,
    get_current_user,
    ALGORITHM,
    SECRET_KEY,
    HTTPAuthorizationCredentials
)


# --- Unit test for created_access_token ---

def test_create_access_token_with_payload():
    """
    Tests that the token contains the correct subject and has an expiration date.
    """

    sub = "123"
    role = "user"

    # Create token 
    token = create_access_token(sub=sub, role=role)

    # Decode token without verification to inspect its contents
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    
    assert decoded_payload["sub"] == "123"
    assert decoded_payload["role"] == "user"
    assert decoded_payload["type"] == "access"
    assert "exp" in decoded_payload



# --- Unit test for supporting int as sub ---

def test_create_access_token_converts_int_subject_to_string():
    """
    Tests that an integer subject is correctly converted to a string.
    """

    sub = 123
    role = "user"

    # Create token 
    token = create_access_token(sub=sub, role=role)
    
    # Decode token without verification to inspect its contents
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert decoded_payload["sub"] == "123"
    assert isinstance(decoded_payload["sub"], str)




# --- Unit test for admin as role ---

def test_create_access_token_with_payload():
    """
    Tests that the token contains the correct role as admin.
    """

    sub = "123"
    role = "admin"

    # Create token 
    token = create_access_token(sub=sub, role=role)

    # Decode token without verification to inspect its contents
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    
    assert decoded_payload["sub"] == "123"
    assert decoded_payload["role"] == "admin"
    assert decoded_payload["type"] == "access"
    assert "exp" in decoded_payload




@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(mocker, mock_users_db):
    """
    Tests that a valid token correctly returns a user using mock data.
    """
    # 1. Get a user from our test fixture
    token_str = create_access_token(sub="123", role="admin")

    # 2. Create a token and credentials for the test user
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)

    # 2. Call the function with the correct object type
    user_payload = await get_current_user(token=mock_credentials)

    assert user_payload["sub"] == "123"
    assert user_payload["role"] == "admin"