def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_user(client):
    response = client.post(
        "/users", json={"email": "a@example.com", "password": "correct-horse-1"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "a@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email(client):
    payload = {"email": "a@example.com", "password": "correct-horse-1"}
    client.post("/users", json=payload)
    response = client.post("/users", json=payload)
    assert response.status_code == 409


def test_register_short_password(client):
    response = client.post(
        "/users", json={"email": "a@example.com", "password": "abc"}
    )
    assert response.status_code == 422


def test_login_wrong_password(client):
    client.post("/users", json={"email": "a@example.com", "password": "correct-horse-1"})
    response = client.post(
        "/login", data={"username": "a@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_tasks_require_login(client):
    response = client.get("/tasks")
    assert response.status_code == 401

def test_cors_allows_frontend_origin(client):
    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_blocks_unknown_origin(client):
    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers