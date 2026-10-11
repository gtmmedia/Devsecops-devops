def test_add_comment_returns_201(client, make_ticket):
    ticket = make_ticket()

    response = client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"author": "Priya", "body": "I've refunded the duplicate charge."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ticket_id"] == ticket["id"]
    assert body["author"] == "Priya"


def test_comments_are_listed_in_order(client, make_ticket):
    ticket = make_ticket()
    for body in ("one", "two", "three"):
        client.post(
            f"/api/tickets/{ticket['id']}/comments",
            json={"author": "Priya", "body": body},
        )

    response = client.get(f"/api/tickets/{ticket['id']}/comments")

    assert response.status_code == 200
    assert [c["body"] for c in response.json()] == ["one", "two", "three"]


def test_comment_on_missing_ticket_returns_404(client):
    response = client.post("/api/tickets/404/comments", json={"author": "x", "body": "y"})
    assert response.status_code == 404


def test_empty_comment_is_rejected(client, make_ticket):
    ticket = make_ticket()
    response = client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"author": "Priya", "body": "   "},
    )
    assert response.status_code == 422


def test_list_shows_comment_count(client, make_ticket):
    ticket = make_ticket()
    client.post(f"/api/tickets/{ticket['id']}/comments", json={"author": "a", "body": "b"})
    client.post(f"/api/tickets/{ticket['id']}/comments", json={"author": "a", "body": "c"})

    listed = client.get("/api/tickets").json()

    assert listed[0]["comment_count"] == 2
