"""Tests du socle V0.2/V0.3 : lecture JSON, recherche, filtres, KPI, qualité.
Utilise un fixture générique (tests/fixtures/sample_services.json), indépendant
de toute donnée métier réelle — l'app elle-même ne contient plus de données hardcodées.
"""
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.json_repository import JsonRepository
from services.service_manager import ServiceManager
from services.statistics import compute_kpis
from services.quality import quality_report, completeness_report

FIXTURE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sample_services.json")


def load_services():
    with open(FIXTURE_FILE, encoding="utf-8") as f:
        return json.load(f)["services"]


def test_fixture_loads():
    services = load_services()
    assert len(services) == 5
    assert all("id" in s for s in services)


def test_repository_read():
    repo = JsonRepository(FIXTURE_FILE)
    data = repo.read()
    assert data["metadata"]["application"] == "MIRSAAD"
    assert len(data["services"]) == 5


def test_repository_write_atomic_and_backup():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = os.path.join(tmpdir, "services.json")
        backups = os.path.join(tmpdir, "backups")
        repo = JsonRepository(target, backups)

        repo.write({"metadata": {}, "services": []}, backup=False)
        assert os.path.exists(target)

        repo.write({"metadata": {}, "services": [{"id": "X"}]}, backup=True)
        assert len(repo.list_backups()) == 1

        data = repo.read()
        assert data["services"][0]["id"] == "X"


def test_manager_get_by_id():
    manager = ServiceManager(JsonRepository(FIXTURE_FILE))
    svc = manager.get_by_id("APP-T01")
    assert svc is not None
    assert svc["identification"]["nom"] == "Portail Démo"


def test_manager_search():
    manager = ServiceManager(JsonRepository(FIXTURE_FILE))
    results = manager.search("MySQL")
    assert len(results) >= 1
    results = manager.search("Portail Démo")
    assert any(s["id"] == "APP-T01" for s in results)


def test_manager_filter_combines_and():
    manager = ServiceManager(JsonRepository(FIXTURE_FILE))
    all_services = manager.get_all()
    filtered = manager.filter(all_services, {"criticite": "Critique", "hebergement": "Cloud"})
    assert len(filtered) == 1
    assert filtered[0]["id"] == "APP-T01"


def test_kpis_total_matches():
    services = load_services()
    kpis = compute_kpis(services)
    assert kpis["total"] == 5
    assert sum(kpis["par_statut_portfolio"].values()) == 5


def test_kpis_empty_services_does_not_crash():
    kpis = compute_kpis([])
    assert kpis["total"] == 0
    assert kpis["par_statut_portfolio"] == {}
    assert kpis["par_criticite"] == {}


def test_quality_report_detects_known_anomalies():
    services = load_services()
    report = quality_report(services)
    assert report["anomalies"]["RTO manquant"] == ["APP-T02", "APP-T03", "APP-T04", "APP-T05"]
    assert report["anomalies"]["RPO manquant"] == ["APP-T03", "APP-T04", "APP-T05"]
    assert report["anomalies"]["Propriétaire manquant"] == ["APP-T02", "APP-T05"]
    assert report["nb_anomalies_total"] == 12


def test_completeness_report_consistent():
    services = load_services()
    report = completeness_report(services)
    assert report["completes"] + report["incompletes"] == report["total"]
    assert report["taux_completude_pct"] == 41


def test_completeness_report_custom_threshold():
    services = load_services()
    report = completeness_report(services, seuil_pct=30)
    assert report["completes"] == 4  # tous sauf APP-T05 (7%)
