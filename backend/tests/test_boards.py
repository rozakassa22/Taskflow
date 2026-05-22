def test_unauthenticated_request_rejected(client):
    assert client.get("/api/boards").status_code == 401


def test_create_board_seeds_default_columns(client, auth_headers):
    resp = client.post("/api/boards", json={"name": "My board"}, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "My board"
    assert len(body["columns"]) == 3
    assert [c["name"] for c in body["columns"]] == ["Todo", "Doing", "Done"]
    assert [c["position"] for c in body["columns"]] == [0, 1, 2]


def test_list_boards_only_returns_owned(client, auth_headers):
    client.post("/api/boards", json={"name": "Mine"}, headers=auth_headers)

    # Different user
    client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "longenough"},
    )
    token = client.post(
        "/api/auth/login",
        json={"email": "other@example.com", "password": "longenough"},
    ).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {token}"}

    mine = client.get("/api/boards", headers=auth_headers).json()
    theirs = client.get("/api/boards", headers=other_headers).json()
    assert len(mine) == 1
    assert mine[0]["name"] == "Mine"
    assert theirs == []


def test_delete_board_cascades(client, auth_headers):
    board_id = client.post(
        "/api/boards", json={"name": "x"}, headers=auth_headers
    ).json()["id"]
    resp = client.delete(f"/api/boards/{board_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/api/boards/{board_id}", headers=auth_headers).status_code == 404


def test_cannot_access_others_board(client, auth_headers):
    board_id = client.post(
        "/api/boards", json={"name": "x"}, headers=auth_headers
    ).json()["id"]

    client.post(
        "/api/auth/register",
        json={"email": "intruder@example.com", "password": "longenough"},
    )
    token = client.post(
        "/api/auth/login",
        json={"email": "intruder@example.com", "password": "longenough"},
    ).json()["access_token"]

    resp = client.get(f"/api/boards/{board_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404
