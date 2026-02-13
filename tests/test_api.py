import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import Base, get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

from app.main import format_duration, format_size
from app.database import UsageLog
from datetime import datetime, timedelta

from app.database import get_db
from app.main import startup_event

def test_get_db_generator():
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass

def test_startup_event():
    # Explicitly call it to cover the function and init_db call
    startup_event()

def test_format_duration():
    assert format_duration(3660) == "1h01m"
    assert format_duration(60) == "0h01m"

def test_format_size():
    assert format_size(500) == "500.00KB"
    assert format_size(2048) == "2.00MB"
    assert format_size(2 * 1024 * 1024) == "2.00GB"

def test_get_analytics_with_data():
    db = TestingSessionLocal()
    # Seed data
    target_date = datetime(2022, 12, 24)
    log = UsageLog(
        username="user1",
        mac_address="mac1",
        start_time=target_date,
        usage_time_seconds=3600,
        upload_kb=1000,
        download_kb=1000
    )
    db.add(log)
    db.commit()
    
    response = client.get("/analytics?date=24122022&pageSize=10&page=1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) > 0
    assert data[0]["username"] == "user1"
    assert data[0]["lastDayUsage"] == "1h00m"

def test_search_user_success():
    db = TestingSessionLocal()
    ref_time = datetime(2022, 11, 4, 15, 43)
    log = UsageLog(
        username="john",
        mac_address="mac1",
        start_time=ref_time - timedelta(minutes=30),
        usage_time_seconds=1800,
        upload_kb=10240, # 10MB
        download_kb=20480 # 20MB
    )
    db.add(log)
    db.commit()

    response = client.get("/user/search?username=john&datetime=20221104T1543")
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert res_data["username"] == "john"
    assert res_data["lastHourUsage"]["time"] == "0h30m"
    assert res_data["lastHourUsage"]["upload"] == "10.00MB"

def test_get_analytics_success():
    response = client.get("/analytics?date=24122022&pageSize=10&page=1")
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_get_analytics_invalid_date():
    response = client.get("/analytics?date=32122022")
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "invalid date"

def test_get_analytics_future_date():
    response = client.get("/analytics?date=01012099")
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "invalid date"

def test_search_user_not_found():
    response = client.get("/user/search?username=nonexistent&datetime=20221104T1543")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "user not found"

def test_search_user_invalid_datetime():
    response = client.get("/user/search?username=john&datetime=invalid")
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "invalid datetime format"
