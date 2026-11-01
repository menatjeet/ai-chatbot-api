def test_register_user_success(client):
    payload = {
        "name": "Alice Wonderland",
        "email": "alice@example.com",
        "password": "Password1234!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email(client, registered_user, test_user_data):
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_register_short_password(client):
    payload = {
        "name": "Short Pass",
        "email": "short@example.com",
        "password": "short"  # < 8 chars
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_register_invalid_email(client):
    payload = {
        "name": "Bad Email",
        "email": "not-an-email",
        "password": "ValidPassword123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_login_success(client, registered_user, test_user_data):
    response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, registered_user, test_user_data):
    response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": "WrongPassword999!"
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_email(client):
    response = client.post("/api/auth/login", json={
        "email": "ghost@example.com",
        "password": "AnyPassword123!"
    })
    assert response.status_code == 401


def test_get_me_success(client, registered_user, test_user_data):
    response = client.get("/api/auth/me", headers=registered_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["name"] == test_user_data["name"]


def test_get_me_unauthorized(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401

    response_bad_token = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer totally_fake_invalid_token"}
    )
    assert response_bad_token.status_code == 401
