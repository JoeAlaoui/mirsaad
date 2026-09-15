"""Tests du socle V0.2 : lecture JSON, recherche, filtres, KPI, qualité."""
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.json_repository import JsonRepository
from services.service_manager import ServiceManager
from services.statistics import compute_kpis
from services.quality import quality_report, completeness_report

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "services.json")


def load_services():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)["services"]


def test_services_json_loads():
    services = load_services()
    assert len(services) == 13
    assert all("id" in s for s in services)


def test_repository_read():
    repo = JsonRepository(DATA_FILE)
    data = repo.read()
    assert data["metadata"]["application"] == "MIRSAAD"
    assert len(data["services"]) == 13


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
    manager = ServiceManager(JsonRepository(DATA_FILE))
    svc = manager.get_by_id("APP-015")
    assert svc is not None
    assert svc["identification"]["nom"] == "Tarkhiss"


def test_manager_search():
    manager = ServiceManager(JsonRepository(DATA_FILE))
    results = manager.search("MySQL")
    assert len(results) >= 1
    results = manager.search("Tarkhiss")
    assert any(s["id"] == "APP-015" for s in results)


def test_manager_filter_combines_and():
    manager = ServiceManager(JsonRepository(DATA_FILE))
    all_services = manager.get_all()
    filtered = manager.filter(all_services, {"criticite": "Critique", "hebergement": "Cloud"})
    for s in filtered:
        assert s["meta"]["criticite"] == "Critique"
        assert s["identification"]["hebergement"] == "Cloud"


def test_kpis_total_matches():
    services = load_services()
    kpis = compute_kpis(services)
    assert kpis["total"] == 13
    assert sum(kpis["par_statut_portfolio"].values()) == 13


def test_quality_report_detects_known_anomalies():
    services = load_services()
    report = quality_report(services)
    # D'après le diagnostic V0.1 : RTO/RPO manquants sur 7 services
    assert "RTO manquant" in report["anomalies"]
    assert len(report["anomalies"]["RTO manquant"]) == 7


def test_completeness_report_consistent():
    services = load_services()
    report = completeness_report(services)
    assert report["completes"] + report["incompletes"] == report["total"]
