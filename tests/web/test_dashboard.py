from fastapi.testclient import TestClient

from observatory.web.app import create_app


def test_dashboard_route_returns_placeholder_counts() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Harnesses" in response.text
    assert "Topics" in response.text
    assert "Insights" in response.text
    assert 'hx-get="/partials/dashboard/pulse"' in response.text


def test_dashboard_htmx_partial_returns_html() -> None:
    client = TestClient(create_app())

    response = client.get("/partials/dashboard/pulse", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "HTMX partial rendered" in response.text
