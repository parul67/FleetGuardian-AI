import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db

# Setup temporary test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency in test environment
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_and_crud():
    # 1. Register a test manager
    reg_payload = {
        "email": "manager@test.com",
        "password": "securepassword",
        "full_name": "Test Manager",
        "role": "manager"
    }
    reg_response = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_response.status_code == 201
    assert reg_response.json()["email"] == "manager@test.com"

    # 2. Login
    login_payload = {
        "email": "manager@test.com",
        "password": "securepassword"
    }
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create driver
    driver_payload = {
        "employee_id": "TEST-D01",
        "name": "Test Driver",
        "license_number": "LIC-9988",
        "phone": "555-1234",
        "email": "driver@test.com",
        "current_status": "active"
    }
    driver_response = client.post("/api/v1/drivers/", json=driver_payload, headers=headers)
    assert driver_response.status_code == 201
    driver_id = driver_response.json()["id"]

    # 4. Get driver
    get_response = client.get(f"/api/v1/drivers/{driver_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Test Driver"
