"""Tests des endpoints API (backend de la SPA).
Utilise le fixture générique tests/fixtures/sample_services.json (config surchargée),
jamais les données réelles d'un client — l'app livrée ne contient plus de données hardcodées.
"""
import os
import sys
import json
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


@pytest.fixture
def client(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "backups").mkdir()

    shutil.copy(os.path.join(FIXTURE_DIR, "sample_services.json"), data_dir / "services.json")

    references = {
        "statut_portfolio": {"values": ["Pipeline", "Catalogue", "Retraité"], "descriptions": {}},
        "criticite": {"values": ["Critique", "Élevée", "Moyenne", "Faible"], "descriptions": {}},
        "hebergement": ["Cloud", "On-premise"],
        "mode_developpement": ["Interne", "Prestataire"],
        "categorie": ["Métier", "Support"],
    }
    (data_dir / "references.json").write_text(json.dumps(references, ensure_ascii=False), encoding="utf-8")

    settings = {
        "organisation_name": "Organisation Test",
        "organisation_name_complete": "",
        "application_name": "MIRSAAD",
        "application_name_ar": "مرصاد",
        "seuil_completude_pct": 70,
        "theme": "institutionnel",
    }
    (data_dir / "settings.json").write_text(json.dumps(settings, ensure_ascii=False), encoding="utf-8")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SERVICES_FILE"] = str(data_dir / "services.json")
    app.config["REFERENCES_FILE"] = str(data_dir / "references.json")
    app.config["SETTINGS_FILE"] = str(data_dir / "settings.json")
    app.config["BACKUPS_DIR"] = str(data_dir / "backups")

    with app.test_client() as c:
        yield c


def test_dashboard_endpoint(client):
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert data["kpis"]["total"] == 5
    assert data["quality"]["nb_anomalies_total"] == 12


def test_services_list(client):
    res = client.get("/api/services")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 5
    assert data["nb_resultats"] == 5


def test_services_search(client):
    res = client.get("/api/services?q=Portail")
    data = res.get_json()
    assert any(s["id"] == "APP-T01" for s in data["services"])


def test_services_combined_filter(client):
    res = client.get("/api/services?criticite=Critique&hebergement=Cloud")
    data = res.get_json()
    assert data["nb_resultats"] == 1
    assert data["services"][0]["id"] == "APP-T01"


def test_service_detail_found(client):
    res = client.get("/api/services/APP-T01")
    assert res.status_code == 200
    assert res.get_json()["identification"]["nom"] == "Portail Démo"


def test_service_detail_not_found(client):
    res = client.get("/api/services/APP-999")
    assert res.status_code == 404


def test_quality_endpoint(client):
    res = client.get("/api/quality")
    data = res.get_json()
    assert len(data["report"]["anomalies"]["RTO manquant"]) == 4


def test_quality_drilldown(client):
    res = client.get("/api/quality?anomalie=" + "Propriétaire manquant")
    data = res.get_json()
    ids = {s["id"] for s in data["services_filtres"]}
    assert ids == {"APP-T02", "APP-T05"}


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


def test_settings_get_default(client):
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.get_json()
    assert data["organisation_name"] == "Organisation Test"
    assert data["application_name"] == "MIRSAAD"


def test_settings_update_organisation_name(client):
    res = client.put("/api/settings", json={"organisation_name": "Nouvelle Agence"})
    assert res.status_code == 200
    assert res.get_json()["organisation_name"] == "Nouvelle Agence"

    res2 = client.get("/api/settings")
    assert res2.get_json()["organisation_name"] == "Nouvelle Agence"


def test_settings_update_rejects_empty_name(client):
    res = client.put("/api/settings", json={"organisation_name": "   "})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_settings_update_rejects_unknown_field(client):
    res = client.put("/api/settings", json={"champ_inexistant": "valeur"})
    assert res.status_code == 400


def test_settings_update_validates_seuil_range(client):
    res = client.put("/api/settings", json={"seuil_completude_pct": 150})
    assert res.status_code == 400


def test_settings_update_accepts_valid_theme(client):
    res = client.put("/api/settings", json={"theme": "moderne"})
    assert res.status_code == 200
    assert res.get_json()["theme"] == "moderne"


def test_settings_update_accepts_ant_theme(client):
    res = client.put("/api/settings", json={"theme": "ant"})
    assert res.status_code == 200
    assert res.get_json()["theme"] == "ant"


def test_settings_update_accepts_pdf_customization(client):
    res = client.put("/api/settings", json={
        "pdf_cover_mode": "texte",
        "pdf_footer_mode": "vide",
        "pdf_custom_text": "Portefeuille de Services",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["pdf_cover_mode"] == "texte"
    assert data["pdf_footer_mode"] == "vide"


def test_settings_update_rejects_unknown_pdf_cover_mode(client):
    res = client.put("/api/settings", json={"pdf_cover_mode": "video"})
    assert res.status_code == 400


def test_settings_update_rejects_unknown_theme(client):
    res = client.put("/api/settings", json={"theme": "inexistant"})
    assert res.status_code == 400


def test_settings_update_creates_backup(client, tmp_path):
    client.put("/api/settings", json={"organisation_name": "Encore Une Autre"})
    backups_dir = tmp_path / "data" / "backups"
    backups = list(backups_dir.glob("settings_*.json"))
    assert len(backups) >= 1


def test_quality_threshold_affects_completeness(client):
    client.put("/api/settings", json={"seuil_completude_pct": 30})
    res = client.get("/api/quality")
    data = res.get_json()
    assert data["report"]["completude"]["seuil_pct"] == 30
    assert data["report"]["completude"]["completes"] == 4


# ---------- Sécurité (V0.9) ----------

def test_import_rejects_unsupported_extension(client):
    from io import BytesIO
    data = {"file": (BytesIO(b"contenu quelconque"), "malware.exe")}
    res = client.post("/api/import/preview", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_import_missing_file_rejected(client):
    res = client.post("/api/import/preview", data={}, content_type="multipart/form-data")
    assert res.status_code == 400


def test_404_error_is_json_for_api_routes(client):
    res = client.get("/api/totally/unknown/route")
    assert res.status_code == 404
    assert res.content_type.startswith("application/json")


# ---------- CRUD (V0.4) ----------

def test_create_service_success(client):
    res = client.post("/api/services", json={"identification": {"nom": "Service API Test"}})
    assert res.status_code == 201
    data = res.get_json()
    assert data["identification"]["nom"] == "Service API Test"
    assert data["id"].startswith("APP-")


def test_create_service_missing_nom(client):
    res = client.post("/api/services", json={"identification": {}})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_create_service_duplicate_name(client):
    res = client.post("/api/services", json={"identification": {"nom": "Portail Démo"}})
    assert res.status_code == 400


def test_create_then_list_shows_new_total(client):
    before = client.get("/api/services").get_json()["total"]
    client.post("/api/services", json={"identification": {"nom": "Encore un service"}})
    after = client.get("/api/services").get_json()["total"]
    assert after == before + 1


def test_update_service_success(client):
    res = client.put("/api/services/APP-T01", json={"identification": {"proprietaire": "API Test Owner"}})
    assert res.status_code == 200
    assert res.get_json()["identification"]["proprietaire"] == "API Test Owner"


def test_update_service_not_found(client):
    res = client.put("/api/services/APP-INEXISTANT", json={"identification": {"nom": "X"}})
    assert res.status_code == 404


def test_delete_service_success(client):
    res = client.delete("/api/services/APP-T01")
    assert res.status_code == 200
    assert res.get_json()["deleted"] is True
    assert client.get("/api/services/APP-T01").status_code == 404


def test_delete_service_not_found(client):
    res = client.delete("/api/services/APP-INEXISTANT")
    assert res.status_code == 404
