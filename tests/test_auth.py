import json


def test_register_success(client):
    response = client.post(
        "/register",
        data=json.dumps({"email": "test@example.com", "password": "password123"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 36


def test_register_missing_email(client):
    response = client.post(
        "/register",
        data=json.dumps({"password": "password123"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Email and password are required" in data["message"]


def test_register_missing_password(client):
    response = client.post(
        "/register",
        data=json.dumps({"email": "test@example.com"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Email and password are required" in data["message"]


def test_register_duplicate_email(client):
    client.post(
        "/register",
        data=json.dumps({"email": "duplicate@example.com", "password": "password123"}),
        content_type="application/json",
    )
    response = client.post(
        "/register",
        data=json.dumps({"email": "duplicate@example.com", "password": "different"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "already exists" in data["message"]


def test_login_success(client):
    client.post(
        "/register",
        data=json.dumps({"email": "login@example.com", "password": "mypassword"}),
        content_type="application/json",
    )
    response = client.post(
        "/login",
        data=json.dumps({"email": "login@example.com", "password": "mypassword"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 36


def test_login_invalid_email(client):
    response = client.post(
        "/login",
        data=json.dumps({"email": "nonexistent@example.com", "password": "password"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid email or password" in data["message"]


def test_login_invalid_password(client):
    client.post(
        "/register",
        data=json.dumps({"email": "user@example.com", "password": "correctpassword"}),
        content_type="application/json",
    )
    response = client.post(
        "/login",
        data=json.dumps({"email": "user@example.com", "password": "wrongpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid email or password" in data["message"]
