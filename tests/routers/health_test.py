from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_health_check(client: TestClient):
    """
    Tests the /health endpoint to ensure the API is running.
    """
    response = client.get("/status/router")
    assert response.status_code == 200
    assert response.json() == {"status": "Router is OK!"}

def test_database_connection_is_mocked(client: TestClient):
    """
    This test implicitly checks if the database connection logic works
    by confirming that an endpoint requiring a DB session can be accessed.
    It relies on the fixtures in conftest.py to handle the DB setup.
    """
    # We use an existing router endpoint that depends on the database
    response = client.get("/status/database") # Assumes this endpoint exists and uses get_db
    
    # A successful response means the test DB session was created and passed to the endpoint
    assert response.status_code == 200
    assert response.json()["status"] == "Database is OK!"