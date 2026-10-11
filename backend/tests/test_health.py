def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_ready_checks_the_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_metrics_endpoint_uses_prometheus_format(client, make_ticket):
    make_ticket()
    client.get("/api/tickets")

    response = client.get("/metrics")

    assert response.status_code == 200
    text = response.text
    assert "# HELP http_requests_total" in text
    assert "quickdesk_tickets_created_total" in text
    # business gauge is computed from the database at scrape time
    assert 'quickdesk_tickets{status="open"} 1.0' in text
