import pytest


@pytest.mark.regression
def test_healthz_returns_request_id_and_server_timing(client):
    response = client.get("/healthz", headers={"X-Request-ID": "observability-test"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "observability-test"
    assert response.headers["Server-Timing"].startswith("app;dur=")


@pytest.mark.regression
def test_healthz_generates_request_id_when_header_is_missing(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert len(response.headers["X-Request-ID"]) == 32
    assert response.headers["Server-Timing"].startswith("app;dur=")

@pytest.mark.regression
def test_request_id_rejects_unsafe_values_and_exposes_policy_headers(client):
    response = client.get("/healthz", headers={"X-Request-ID": "unsafe id"})
    assert response.status_code == 200
    generated_id = response.headers["X-Request-ID"]
    assert len(generated_id) == 32
    assert " " not in generated_id
    assert response.headers["Permissions-Policy"] == "geolocation=(), microphone=(), camera=()"
