"""Tests for instrument API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Create a test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Tests for health and root endpoints."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()


class TestBondEndpoints:
    """Tests for bond CRUD operations."""

    def test_create_bond(self, client):
        """Test creating a new bond."""
        bond_data = {
            "isin": "US912810TZ99",
            "notional": 1000000.00,
            "currency": "USD",
            "coupon_rate": 0.0375,
            "maturity_date": "2030-01-15",
            "issue_date": "2024-01-15",
            "payment_frequency": "SEMI_ANNUAL",
            "day_count_convention": "ACT_ACT",
        }
        response = client.post("/api/v1/instruments/bonds", json=bond_data)
        assert response.status_code == 201
        data = response.json()
        assert data["isin"] == "US912810TZ99"
        assert data["instrument_type"] == "BOND"
        assert "id" in data

    def test_create_bond_duplicate_isin(self, client):
        """Test creating a bond with duplicate ISIN fails."""
        bond_data = {
            "isin": "US912810TA00",
            "notional": 1000000.00,
            "coupon_rate": 0.0375,
            "maturity_date": "2030-01-15",
        }
        response = client.post("/api/v1/instruments/bonds", json=bond_data)
        assert response.status_code == 201

        response = client.post("/api/v1/instruments/bonds", json=bond_data)
        assert response.status_code == 409

    def test_create_bond_invalid_coupon(self, client):
        """Test creating a bond with invalid coupon rate fails."""
        bond_data = {
            "isin": "US912810TB00",
            "notional": 1000000.00,
            "coupon_rate": 1.5,  # Invalid: > 1
            "maturity_date": "2030-01-15",
        }
        response = client.post("/api/v1/instruments/bonds", json=bond_data)
        assert response.status_code == 422

    def test_get_bond(self, client):
        """Test getting a bond by ID."""
        # Create bond first
        bond_data = {
            "isin": "US912810TC00",
            "notional": 1000000.00,
            "coupon_rate": 0.0375,
            "maturity_date": "2030-01-15",
        }
        create_response = client.post("/api/v1/instruments/bonds", json=bond_data)
        bond_id = create_response.json()["id"]

        # Get bond
        response = client.get(f"/api/v1/instruments/bonds/{bond_id}")
        assert response.status_code == 200
        assert response.json()["isin"] == "US912810TC00"

    def test_get_bond_not_found(self, client):
        """Test getting non-existent bond returns 404."""
        response = client.get("/api/v1/instruments/bonds/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestSwapEndpoints:
    """Tests for swap CRUD operations."""

    def test_create_swap(self, client):
        """Test creating a new swap."""
        swap_data = {
            "notional": 10000000.00,
            "currency": "USD",
            "fixed_rate": 0.0410,
            "tenor": "5Y",
            "trade_date": "2024-01-15",
            "maturity_date": "2029-01-15",
            "effective_date": "2024-01-17",
            "pay_receive": "PAY",
            "float_index": "SOFR",
            "payment_frequency": "QUARTERLY",
        }
        response = client.post("/api/v1/instruments/swaps", json=swap_data)
        assert response.status_code == 201
        data = response.json()
        assert data["instrument_type"] == "SWAP"
        assert data["tenor"] == "5Y"
        assert data["pay_receive"] == "PAY"

    def test_create_swap_invalid_dates(self, client):
        """Test creating swap with maturity before trade date fails."""
        swap_data = {
            "notional": 10000000.00,
            "fixed_rate": 0.0410,
            "tenor": "5Y",
            "trade_date": "2024-01-15",
            "maturity_date": "2023-01-15",  # Before trade date
            "pay_receive": "PAY",
        }
        response = client.post("/api/v1/instruments/swaps", json=swap_data)
        assert response.status_code == 422

    def test_get_swap(self, client):
        """Test getting a swap by ID."""
        swap_data = {
            "notional": 10000000.00,
            "fixed_rate": 0.0410,
            "tenor": "5Y",
            "trade_date": "2024-01-15",
            "maturity_date": "2029-01-15",
            "pay_receive": "RECEIVE",
        }
        create_response = client.post("/api/v1/instruments/swaps", json=swap_data)
        swap_id = create_response.json()["id"]

        response = client.get(f"/api/v1/instruments/swaps/{swap_id}")
        assert response.status_code == 200
        assert response.json()["pay_receive"] == "RECEIVE"


class TestInstrumentListEndpoints:
    """Tests for instrument listing and generic operations."""

    def test_list_instruments_empty(self, client):
        """Test listing instruments when empty."""
        response = client.get("/api/v1/instruments")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_instruments_with_data(self, client):
        """Test listing instruments with data."""
        # Create a bond and a swap
        client.post("/api/v1/instruments/bonds", json={
            "isin": "US912810TD00",
            "notional": 1000000.00,
            "coupon_rate": 0.0375,
            "maturity_date": "2030-01-15",
        })
        client.post("/api/v1/instruments/swaps", json={
            "notional": 10000000.00,
            "fixed_rate": 0.0410,
            "tenor": "5Y",
            "trade_date": "2024-01-15",
            "maturity_date": "2029-01-15",
            "pay_receive": "PAY",
        })

        response = client.get("/api/v1/instruments")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_list_instruments_filter_by_type(self, client):
        """Test filtering instruments by type."""
        # Create a bond and a swap
        client.post("/api/v1/instruments/bonds", json={
            "isin": "US912810TE00",
            "notional": 1000000.00,
            "coupon_rate": 0.0375,
            "maturity_date": "2030-01-15",
        })
        client.post("/api/v1/instruments/swaps", json={
            "notional": 10000000.00,
            "fixed_rate": 0.0410,
            "tenor": "5Y",
            "trade_date": "2024-01-15",
            "maturity_date": "2029-01-15",
            "pay_receive": "PAY",
        })

        # Filter by BOND
        response = client.get("/api/v1/instruments?instrument_type=BOND")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["instrument_type"] == "BOND"

    def test_delete_instrument(self, client):
        """Test deleting an instrument."""
        # Create a bond
        create_response = client.post("/api/v1/instruments/bonds", json={
            "isin": "US912810TF00",
            "notional": 1000000.00,
            "coupon_rate": 0.0375,
            "maturity_date": "2030-01-15",
        })
        bond_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/api/v1/instruments/{bond_id}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/api/v1/instruments/{bond_id}")
        assert response.status_code == 404

    def test_delete_instrument_not_found(self, client):
        """Test deleting non-existent instrument returns 404."""
        response = client.delete("/api/v1/instruments/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
