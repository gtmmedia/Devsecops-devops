import pytest


def test_create_ticket_returns_201_with_defaults(client, ticket_payload):
    del ticket_payload["priority"]

    response = client.post("/api/tickets", json=ticket_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["status"] == "open"
    assert body["priority"] == "medium"
    assert body["assignee"] is None


@pytest.mark.parametrize(
    "bad_fields",
    [
        {"title": "ab"},  # too short
        {"requester_email": "not-an-email"},
        {"priority": "urgent"},  # not low/medium/high
        {"description": ""},
    ],
)
def test_create_ticket_rejects_invalid_input(client, ticket_payload, bad_fields):
    response = client.post("/api/tickets", json={**ticket_payload, **bad_fields})
    assert response.status_code == 422


def test_list_tickets_newest_first(client, make_ticket):
    first = make_ticket(title="First ticket")
    second = make_ticket(title="Second ticket")

    response = client.get("/api/tickets")

    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert ids == [second["id"], first["id"]]


def test_list_tickets_filters_by_status_priority_and_search(client, make_ticket):
    make_ticket(title="Printer is on fire", priority="high")
    low = make_ticket(title="Change my avatar", priority="low")
    client.put(
        f"/api/tickets/{low['id']}",
        json={
            "title": low["title"],
            "description": low["description"],
            "status": "resolved",
            "priority": "low",
            "assignee": None,
        },
    )

    assert len(client.get("/api/tickets?status=resolved").json()) == 1
    assert len(client.get("/api/tickets?priority=high").json()) == 1
    assert len(client.get("/api/tickets?q=printer").json()) == 1
    assert client.get("/api/tickets?q=nothing-matches").json() == []


def test_list_tickets_rejects_unknown_status(client):
    assert client.get("/api/tickets?status=banana").status_code == 422


def test_get_ticket_includes_comments(client, make_ticket):
    ticket = make_ticket()
    client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"author": "Priya", "body": "Looking into it."},
    )

    response = client.get(f"/api/tickets/{ticket['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == ticket["title"]
    assert [c["author"] for c in body["comments"]] == ["Priya"]


def test_get_missing_ticket_returns_404(client):
    response = client.get("/api/tickets/9999")
    assert response.status_code == 404
    assert "9999" in response.json()["detail"]


def test_update_ticket_replaces_editable_fields(client, make_ticket):
    ticket = make_ticket()

    response = client.put(
        f"/api/tickets/{ticket['id']}",
        json={
            "title": "Invoice amount is wrong (March)",
            "description": ticket["description"],
            "status": "in_progress",
            "priority": "medium",
            "assignee": "Rahul",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["assignee"] == "Rahul"
    assert body["priority"] == "medium"


def test_update_with_blank_assignee_unassigns(client, make_ticket):
    ticket = make_ticket()
    payload = {
        "title": ticket["title"],
        "description": ticket["description"],
        "status": "open",
        "priority": "high",
        "assignee": "Rahul",
    }
    client.put(f"/api/tickets/{ticket['id']}", json=payload)

    response = client.put(f"/api/tickets/{ticket['id']}", json={**payload, "assignee": ""})

    assert response.json()["assignee"] is None


def test_update_requires_every_field_because_put_replaces(client, make_ticket):
    ticket = make_ticket()
    response = client.put(f"/api/tickets/{ticket['id']}", json={"status": "closed"})
    assert response.status_code == 422


def test_closed_ticket_is_frozen_until_reopened(client, make_ticket):
    ticket = make_ticket()
    base = {
        "title": ticket["title"],
        "description": ticket["description"],
        "priority": "high",
        "assignee": None,
    }
    assert (
        client.put(f"/api/tickets/{ticket['id']}", json={**base, "status": "closed"}).status_code
        == 200
    )

    # editing while it stays closed is rejected
    edit = client.put(
        f"/api/tickets/{ticket['id']}",
        json={**base, "title": "Sneaky edit", "status": "closed"},
    )
    assert edit.status_code == 409

    # reopening is allowed
    reopen = client.put(f"/api/tickets/{ticket['id']}", json={**base, "status": "open"})
    assert reopen.status_code == 200
    assert reopen.json()["status"] == "open"


def test_delete_ticket_returns_204_and_removes_comments(client, make_ticket):
    ticket = make_ticket()
    client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"author": "Priya", "body": "Hello"},
    )

    response = client.delete(f"/api/tickets/{ticket['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/tickets/{ticket['id']}").status_code == 404
    assert client.get(f"/api/tickets/{ticket['id']}/comments").status_code == 404


def test_delete_missing_ticket_returns_404(client):
    assert client.delete("/api/tickets/12345").status_code == 404


def test_stats_counts_tickets_by_status(client, make_ticket):
    make_ticket(priority="high")
    done = make_ticket(priority="low")
    client.put(
        f"/api/tickets/{done['id']}",
        json={
            "title": done["title"],
            "description": done["description"],
            "status": "resolved",
            "priority": "low",
            "assignee": None,
        },
    )

    stats = client.get("/api/tickets/stats").json()

    assert stats["total"] == 2
    assert stats["open"] == 1
    assert stats["resolved"] == 1
    assert stats["closed"] == 0
    assert stats["high_priority_open"] == 1
