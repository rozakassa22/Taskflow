def test_register_creates_user(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "password": "longenough"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "a@example.com"
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate(client):
    payload = {"email": "dup@example.com", "password": "longenough"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/auth/register", json={"email": "x@example.com", "password": "short"}
    )
    assert resp.status_code == 422


def test_login_returns_token(client):
    client.post(
        "/api/auth/register",
        json={"email": "l@example.com", "password": "longenough"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "l@example.com", "password": "longenough"},
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert resp.json()["access_token"]


def test_login_rejects_bad_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "bad@example.com", "password": "longenough"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "bad@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401
