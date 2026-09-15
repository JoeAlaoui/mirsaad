"""Tests des endpoints API (backend de la SPA)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_dashboard_endpoint(client):
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert data["kpis"]["total"] == 13
    assert "anomalies" in data["quality"]


def test_services_list(client):
    res = client.get("/api/services")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 13
    assert data["nb_resultats"] == 13


def test_services_search(client):
    res = client.get("/api/services?q=Tarkhiss")
    data = res.get_json()
    assert any(s["id"] == "APP-015" for s in data["services"])


def test_services_combined_filter(client):
    res = client.get("/api/services?criticite=Critique&hebergement=Cloud")
    data = res.get_json()
    assert data["nb_resultats"] == 2
    ids = {s["id"] for s in data["services"]}
    assert ids == {"APP-006", "APP-015"}


def test_service_detail_found(client):
    res = client.get("/api/services/APP-015")
    assert res.status_code == 200
    assert res.get_json()["identification"]["nom"] == "Tarkhiss"


def test_service_detail_not_found(client):
    res = client.get("/api/services/APP-999")
    assert res.status_code == 404


def test_quality_endpoint(client):
    res = client.get("/api/quality")
    data = res.get_json()
    assert data["report"]["anomalies"]["RTO manquant"].__len__() == 7


def test_references_endpoint(client):
    res = client.get("/api/references")
    assert res.status_code == 200
    assert "criticite" in res.get_json()


def test_spa_shell_served_for_frontend_routes(client):
    for path in ["/", "/portefeuille", "/qualite", "/route/inexistante"]:
        res = client.get(path)
        assert res.status_code == 200
        assert b'id="app"' in res.data


def test_api_404_returns_json(client):
    res = client.get("/api/route-inexistante")
    assert res.status_code == 404
    assert res.get_json()["error"]
