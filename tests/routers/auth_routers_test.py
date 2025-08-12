from fastapi.testclient import TestClient
from fastapi import status




# --- Test fixtures ---
BASE_ROUTE_URL = "/api/auth"


# --- Integration Tests for Signup Endpoint ---

def test_signup_successful(client: TestClient):
    """
    Tests the "happy path" for user signup, expecting a 201 Created response.
    """
    response = client.post(
        f"{BASE_ROUTE_URL}/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "ValidPassword123!"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["message"] == "User created successfully"
    assert data["detail"]["username"] == "testuser"
    assert data["detail"]["email"] == "test@example.com"
    assert "id" in data["detail"]




def test_signup_with_duplicate_username(client: TestClient):
    """
    Tests that signing up with an existing username returns a 400 Bad Request error.
    """
    # First, create the user
    client.post(
        f"{BASE_ROUTE_URL}/signup",
        json={"username": "existinguser", "email": "exists@example.com", "password": "ValidPassword123!"}
    )
    
    # Then, try to create them again with a different email
    response = client.post(
        "/auth/signup",
        json={"username": "existinguser", "email": "another@example.com", "password": "ValidPassword123!"}
    )
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Username already registered" in response.json()["detail"]




def test_signup_with_duplicate_email(client: TestClient):
    """
    Tests that signing up with an existing username returns a 400 Bad Request error.
    """
    # First, create the user
    client.post(
        f"{BASE_ROUTE_URL}/signup",
        json={"username": "existinguser_1", "email": "exists@example.com", "password": "ValidPassword123!"}
    )
    
    # Then, try to create another user with same email
    response = client.post(
        f"{BASE_ROUTE_URL}/signup",
        json={"username": "existinguser_2", "email": "exists@example.com", "password": "ValidPassword123!"}
    )
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Email already registered" in response.json()["detail"]




def test_signup_with_invalid_email(client: TestClient):
    """
    Tests that the Pydantic validator catches a malformed email, returning a 409 error.
    """
    response = client.post(
        "/auth/signup",
        json={"username": "newuser", "email": "not-a-valid-email", "password": "ValidPassword123!"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY





def test_signup_with_missing_field_username(client: TestClient):
    """
    Tests that Pydantic validation rejects a request with a missing required field.
    """
    response = client.post(
        "/auth/signup",
        json={"email": "another@example.com", "password":"ValidPassword123!"} # username is missing
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY




def test_signup_with_missing_field_email(client: TestClient):
    """
    Tests that Pydantic validation rejects a request with a missing required field.
    """
    response = client.post(
        "/auth/signup",
        json={"username": "anotheruser", "password":"ValidPassword123!"} # email is missing
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY




def test_signup_with_missing_field_password(client: TestClient):
    """
    Tests that Pydantic validation rejects a request with a missing required field.
    """
    response = client.post(
        "/auth/signup",
        json={"username": "anotheruser", "email": "another@example.com"} # Password is missing
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY




# # --- Integration Tests for Login Endpoint ---

def test_login_successful(client: TestClient):
    """
    Tests the "happy path" for user login, expecting a 200 OK response and a token.
    """
    # First, create a user to log in with
    user_credentials = {"username": "loginuser", "email": "login@example.com", "password": "ValidPassword123!"}
    client.post(f"{BASE_ROUTE_URL}/signup", json=user_credentials)
    
    # Now, attempt to log in
    response = client.post(
        f"{BASE_ROUTE_URL}/login",
        json={"username": user_credentials["username"], "password": user_credentials["password"]}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"




def test_login_with_incorrect_password(client: TestClient):
    """
    Tests that the endpoint rejects a valid user with the wrong password, returning 401.
    """
    user_credentials = {"username": "wrongpassuser", "email": "wrongpass@example.com", "password": "ValidPassword123!"}
    client.post(f"{BASE_ROUTE_URL}/signup", json=user_credentials)
    
    # This password is still wrong, but it passes format validation,
    # allowing the test to correctly check the actual login logic.
    response = client.post(
        f"{BASE_ROUTE_URL}/login",
        json={"username": user_credentials["username"], "password": "An-Incorrect-Password99!"}
    )
    
    # Assert the correct error for failed authentication
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid credentials" in response.json()["detail"]




def test_login_with_nonexistent_user(client: TestClient):
    """
    Tests that the endpoint rejects a login attempt for a user that does not exist.
    """
    response = client.post(
        "/auth/login",
        json={"username": "ghostuser", "password": "ValidPassword123!"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED




# def test_signup_sql_injection_attempt(client: TestClient):
#     """
#     Test that signup rejects usernames and emails containing SQL injection patterns.
#     """
#     malicious_payloads = [
#         "'; DROP TABLE users; --",
#         "admin' OR '1'='1",
#         "'; EXEC xp_cmdshell('dir'); --",
#         "'); DELETE FROM users WHERE 'a'='a"
#     ]
#     for payload in malicious_payloads:
#         response = client.post(
#             f"{BASE_ROUTE_URL}/signup",
#             json={
#                 "username": payload,
#                 "email": f"{payload}@example.com",
#                 "password": "ValidPassword123!"
#             }
#         )
#         # Assuming your app returns 422 for invalid input or sanitizes properly
#         assert response.status_code in (400, 422), f"SQL Injection attempt passed: {payload}"