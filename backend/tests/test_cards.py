import pytest


@pytest.fixture
def board(client, auth_headers):
    return client.post(
        "/api/boards", json={"name": "Test"}, headers=auth_headers
    ).json()


def test_create_card_assigns_position(client, auth_headers, board):
    col = board["columns"][0]
    a = client.post(
        f"/api/columns/{col['id']}/cards",
        json={"title": "First"},
        headers=auth_headers,
    ).json()
    b = client.post(
        f"/api/columns/{col['id']}/cards",
        json={"title": "Second"},
        headers=auth_headers,
    ).json()
    assert a["position"] == 0
    assert b["position"] == 1


def test_move_card_to_different_column(client, auth_headers, board):
    todo, doing, _ = board["columns"]
    card = client.post(
        f"/api/columns/{todo['id']}/cards",
        json={"title": "Move me"},
        headers=auth_headers,
    ).json()

    resp = client.patch(
        f"/api/cards/{card['id']}/move",
        json={"column_id": doing["id"], "position": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    moved = resp.json()
    assert moved["column_id"] == doing["id"]
    assert moved["position"] == 0


def test_move_card_within_column_reorders(client, auth_headers, board):
    col = board["columns"][0]
    a = client.post(
        f"/api/columns/{col['id']}/cards",
        json={"title": "A"},
        headers=auth_headers,
    ).json()
    b = client.post(
        f"/api/columns/{col['id']}/cards",
        json={"title": "B"},
        headers=auth_headers,
    ).json()
    c = client.post(
        f"/api/columns/{col['id']}/cards",
        json={"title": "C"},
        headers=auth_headers,
    ).json()

    # Move A to position 2 (the end)
    client.patch(
        f"/api/cards/{a['id']}/move",
        json={"column_id": col["id"], "position": 2},
        headers=auth_headers,
    )

    board_after = client.get(f"/api/boards/{board['id']}", headers=auth_headers).json()
    card_order = [card["title"] for card in board_after["columns"][0]["cards"]]
    assert card_order == ["B", "C", "A"]


def test_delete_card_closes_gap(client, auth_headers, board):
    col = board["columns"][0]
    ids = []
    for title in ["A", "B", "C"]:
        ids.append(
            client.post(
                f"/api/columns/{col['id']}/cards",
                json={"title": title},
                headers=auth_headers,
            ).json()["id"]
        )

    client.delete(f"/api/cards/{ids[0]}", headers=auth_headers)

    board_after = client.get(f"/api/boards/{board['id']}", headers=auth_headers).json()
    cards = board_after["columns"][0]["cards"]
    assert [c["title"] for c in cards] == ["B", "C"]
    assert [c["position"] for c in cards] == [0, 1]
