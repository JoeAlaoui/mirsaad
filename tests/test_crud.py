"""Tests du CRUD d'écriture (V0.4) : création, modification, suppression, validations."""
import os
import sys
import json
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from services.json_repository import JsonRepository
from services.service_manager import ServiceManager
from services.validation import ServiceValidationError

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

REFERENCES = {
    "statut_portfolio": {"values": ["Pipeline", "Catalogue", "Retraité"]},
    "criticite": {"values": ["Critique", "Élevée", "Moyenne", "Faible"]},
    "statut": {"values": ["En production", "En projet", "Obsolète / Arrêt"]},
    "hebergement": ["Cloud", "On-premise"],
    "mode_developpement": ["Interne", "Prestataire"],
    "categorie": ["Métier", "Support"],
}


@pytest.fixture
def manager(tmp_path):
    services_file = tmp_path / "services.json"
    shutil.copy(os.path.join(FIXTURE_DIR, "sample_services.json"), services_file)
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()

    references_file = tmp_path / "references.json"
    references_file.write_text(json.dumps(REFERENCES, ensure_ascii=False), encoding="utf-8")

    repo = JsonRepository(str(services_file), str(backups_dir))
    refs_repo = JsonRepository(str(references_file))
    m = ServiceManager(repo)
    m._refs_repo = refs_repo  # pratique pour les tests
    return m


def test_create_generates_id_when_missing(manager):
    svc = manager.create({"identification": {"nom": "Nouveau Service"}}, references_repository=manager._refs_repo)
    assert svc["id"] == "APP-T06" or svc["id"].startswith("APP-")  # dépend des IDs du fixture (APP-T0x)
    assert svc["identification"]["nom"] == "Nouveau Service"
    assert svc["meta"]["completude_pct"] >= 0


def test_create_requires_nom(manager):
    with pytest.raises(ServiceValidationError):
        manager.create({"identification": {}}, references_repository=manager._refs_repo)


def test_create_rejects_duplicate_name(manager):
    with pytest.raises(ServiceValidationError):
        manager.create({"identification": {"nom": "Portail Démo"}}, references_repository=manager._refs_repo)


def test_create_rejects_duplicate_id(manager):
    with pytest.raises(ServiceValidationError):
        manager.create({"id": "APP-T01", "identification": {"nom": "Autre nom"}}, references_repository=manager._refs_repo)


def test_create_rejects_unknown_reference_value(manager):
    with pytest.raises(ServiceValidationError):
        manager.create(
            {"identification": {"nom": "Test Criticité", "hebergement": "Hybride-Inexistant"}},
            references_repository=manager._refs_repo,
        )


def test_create_persists_and_increments_total(manager):
    before = len(manager.get_all())
    manager.create({"identification": {"nom": "Service Ajouté"}}, references_repository=manager._refs_repo)
    after = manager.get_all()
    assert len(after) == before + 1
    assert any(s["identification"]["nom"] == "Service Ajouté" for s in after)


def test_create_writes_backup(manager, tmp_path):
    manager.create({"identification": {"nom": "Backup Test"}}, references_repository=manager._refs_repo)
    backups = list((tmp_path / "backups").glob("services_*.json"))
    assert len(backups) >= 1


def test_update_existing_service(manager):
    updated = manager.update("APP-T01", {"identification": {"proprietaire": "Nouveau Propriétaire"}}, references_repository=manager._refs_repo)
    assert updated["identification"]["proprietaire"] == "Nouveau Propriétaire"
    assert updated["identification"]["nom"] == "Portail Démo"  # champ non modifié conservé


def test_update_recomputes_completeness(manager):
    before = manager.get_by_id("APP-T05")["meta"]["completude_pct"]
    updated = manager.update(
        "APP-T05",
        {"identification": {"proprietaire": "X", "direction_beneficiaire": "Y"}, "meta": {"criticite": "Faible"}},
        references_repository=manager._refs_repo,
    )
    assert updated["meta"]["completude_pct"] > before


def test_update_nonexistent_returns_none(manager):
    result = manager.update("APP-INEXISTANT", {"identification": {"nom": "X"}}, references_repository=manager._refs_repo)
    assert result is None


def test_update_rejects_duplicate_name_with_other_service(manager):
    with pytest.raises(ServiceValidationError):
        manager.update("APP-T02", {"identification": {"nom": "Portail Démo"}}, references_repository=manager._refs_repo)


def test_update_allows_keeping_own_name(manager):
    # Ne doit pas lever d'erreur : le nom "Portail Démo" appartient déjà à APP-T01
    updated = manager.update("APP-T01", {"identification": {"nom": "Portail Démo"}}, references_repository=manager._refs_repo)
    assert updated["identification"]["nom"] == "Portail Démo"


def test_delete_existing_service(manager):
    before = len(manager.get_all())
    result = manager.delete("APP-T01")
    assert result is True
    assert len(manager.get_all()) == before - 1
    assert manager.get_by_id("APP-T01") is None


def test_delete_nonexistent_returns_false(manager):
    assert manager.delete("APP-INEXISTANT") is False


def test_delete_writes_backup(manager, tmp_path):
    manager.delete("APP-T01")
    backups = list((tmp_path / "backups").glob("services_*.json"))
    assert len(backups) >= 1
