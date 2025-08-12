import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import sys

# --- Path Setup ---
# This ensures that the 'app' directory is in the Python path
# so that its modules can be imported by the test suite.
# This is the most reliable way to handle imports in tests.
APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, APP_DIR)
# --- End Path Setup ---

# Set environment variables for testing BEFORE importing your app modules
load_dotenv()
os.environ["DB_NAME"] = "mvnest_test"

# Now import your app and db components
from app.config import app        # Should import from 'app/config.py'
from app.db import get_db   # Should import from 'app/db.py'
from app.models.models import Base

# Use a separate database URL for testing
TEST_DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)




@pytest.fixture(scope="session", autouse=True)
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()




app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c




@pytest.fixture(scope="module")
def mock_users_db():
    """
    Provides a dictionary of mock users for testing get_current_user function.
    """
    return {
        "test_admin": {"sub": "123", "role": "admin", "email": "admin@movienest.com"},
        "test_user": {"sub": "43", "role": "user", "email": "test@movienest.com"}
    }

