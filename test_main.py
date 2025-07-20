import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from models import User, Player, Team, Gameweek
from auth import get_password_hash

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

@pytest.fixture
def client():
    # Create test database
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(client):
    """Create a test user."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    return response.json()

@pytest.fixture
def test_admin_user(client):
    """Create a test admin user."""
    # Create admin user directly in database
    db = TestingSessionLocal()
    admin_user = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        role="admin"
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    db.close()
    
    # Login to get token
    response = client.post("/auth/login", data={
        "username": "admin@example.com",
        "password": "adminpassword123"
    })
    assert response.status_code == 200
    return response.json()

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post("/auth/login", data={
        "username": test_user["email"],
        "password": "testpassword123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, test_admin_user):
    """Get authentication headers for admin user."""
    token = test_admin_user["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Fantasy Football API is running!"}

def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_user_registration(client):
    """Test user registration."""
    user_data = {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "newpassword123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]
    assert response.json()["name"] == user_data["name"]

def test_user_login(client, test_user):
    """Test user login."""
    response = client.post("/auth/login", data={
        "username": test_user["email"],
        "password": "testpassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_get_current_user(client, auth_headers):
    """Test getting current user profile."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_create_player_admin_only(client, admin_headers):
    """Test creating a player (admin only)."""
    player_data = {
        "name": "Test Player",
        "position": "midfielder",
        "team": "Test FC",
        "price": 7.5
    }
    response = client.post("/players/", json=player_data, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == player_data["name"]
    assert response.json()["position"] == player_data["position"]

def test_create_player_unauthorized(client, auth_headers):
    """Test creating a player without admin rights."""
    player_data = {
        "name": "Test Player",
        "position": "midfielder",
        "team": "Test FC",
        "price": 7.5
    }
    response = client.post("/players/", json=player_data, headers=auth_headers)
    assert response.status_code == 403

def test_create_team(client, auth_headers):
    """Test creating a team."""
    team_data = {
        "name": "My Fantasy Team"
    }
    response = client.post("/teams/", json=team_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == team_data["name"]

def test_create_gameweek(client, admin_headers):
    """Test creating a gameweek."""
    gameweek_data = {
        "number": 1,
        "deadline": "2024-01-01T12:00:00"
    }
    response = client.post("/gameweeks/", json=gameweek_data, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["number"] == gameweek_data["number"]

def test_create_league(client, auth_headers):
    """Test creating a league."""
    league_data = {
        "name": "Test League",
        "is_private": True
    }
    response = client.post("/leagues/", json=league_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == league_data["name"]
    assert "code" in response.json()

def test_unauthorized_access(client):
    """Test accessing protected endpoints without authentication."""
    response = client.get("/users/me")
    assert response.status_code == 401

def test_get_players(client, auth_headers):
    """Test getting players list."""
    response = client.get("/players/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_gameweeks(client, auth_headers):
    """Test getting gameweeks list."""
    response = client.get("/gameweeks/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

if __name__ == "__main__":
    pytest.main([__file__]) 