import json


def test_fetch_stats_invalid_user(client):
    response = client.get("/stats/nonexistent-id")
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid user ID" in data["message"]


def test_save_stat_invalid_user(client):
    response = client.post(
        "/stats/nonexistent-id/save",
        data=json.dumps({"prompts": 10, "water": 5}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid user ID" in data["message"]


def test_save_and_fetch_stats(client):
    register_response = client.post(
        "/register",
        data=json.dumps({"email": "stats@example.com", "password": "password123"}),
        content_type="application/json",
    )
    user_id = register_response.get_json()

    save_response = client.post(
        f"/stats/{user_id}/save",
        data=json.dumps({"prompts": 10, "water": 5, "co2": 3, "power": 2}),
        content_type="application/json",
    )
    assert save_response.status_code == 200

    fetch_response = client.get(f"/stats/{user_id}")
    assert fetch_response.status_code == 200
    data = fetch_response.get_json()
    assert data["total"]["prompts"] == 10
    assert data["total"]["water"] == 5
    assert data["total"]["co2"] == 3
    assert data["total"]["power"] == 2


def test_save_stat_accumulates(client):
    register_response = client.post(
        "/register",
        data=json.dumps({"email": "accumulate@example.com", "password": "password"}),
        content_type="application/json",
    )
    user_id = register_response.get_json()

    client.post(
        f"/stats/{user_id}/save",
        data=json.dumps({"prompts": 5}),
        content_type="application/json",
    )
    client.post(
        f"/stats/{user_id}/save",
        data=json.dumps({"prompts": 3}),
        content_type="application/json",
    )

    fetch_response = client.get(f"/stats/{user_id}")
    data = fetch_response.get_json()
    assert data["total"]["prompts"] == 8


def test_worldwide_stats_empty(client):
    response = client.get("/stats/worldwide")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"]["prompts"] == 0
    assert data["total"]["water"] == 0
    assert data["total"]["co2"] == 0
    assert data["total"]["power"] == 0
