from app.models.enums import UserRole


def test_user_registration(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "strongpassword123",
            "full_name": "Test Citizen",
            "role": "Citizen"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "Citizen"
    assert "id" in data


def test_user_login_success(client, citizen_user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": citizen_user.email,
            "password": "citizen_pass_123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "Citizen"
    assert data["user_id"] == citizen_user.id


def test_user_login_invalid_password(client, citizen_user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": citizen_user.email,
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_get_current_user_profile(client, citizen_token, citizen_user):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == citizen_user.id
    assert data["email"] == citizen_user.email


def test_get_current_user_unauthorized(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 403 or response.status_code == 401
