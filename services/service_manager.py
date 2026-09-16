"""
Logique métier sur les services : accès, recherche, filtres.
CRUD d'écriture (add/update/delete) prévu pour V0.4 — lecture seule pour le socle V0.2/V0.3.
"""

import re
import copy

from services.quality import compute_completude_pct
from services.validation import validate_service_record

SEARCHABLE_PATHS = [
    ("id",),
    ("identification", "nom"),
    ("identification", "proprietaire"),
    ("identification", "direction_beneficiaire"),
    ("identification", "prestataire"),
    ("proposition_valeur", "objectif"),
    ("description", "fonctionnelle"),
    ("architecture", "stack_technologique"),
    ("architecture", "donnees_traitees"),
]

FILTERABLE_FIELDS = {
    "categorie": ("identification", "categorie"),
    "mode_developpement": ("identification", "mode_developpement"),
    "prestataire": ("identification", "prestataire"),
    "statut_portfolio": ("identification", "statut_portfolio"),
    "hebergement": ("identification", "hebergement"),
    "proprietaire": ("identification", "proprietaire"),
    "direction_beneficiaire": ("identification", "direction_beneficiaire"),
    "statut": ("meta", "statut"),
    "criticite": ("meta", "criticite"),
}


def _get_path(svc, path):
    v = svc
    for key in path:
        if not isinstance(v, dict):
            return None
        v = v.get(key)
    return v


class ServiceManager:
    def __init__(self, repository):
        self.repository = repository

    def get_all(self):
        return self.repository.read()["services"]

    def get_by_id(self, service_id):
        for svc in self.get_all():
            if svc["id"] == service_id:
                return svc
        return None

    def search(self, query):
        """Recherche globale insensible à la casse sur les champs textuels principaux."""
        if not query:
            return self.get_all()
        q = query.strip().lower()
        results = []
        for svc in self.get_all():
            for path in SEARCHABLE_PATHS:
                val = _get_path(svc, path)
                if val and q in str(val).lower():
                    results.append(svc)
                    break
        return results

    def filter(self, services, filters):
        """filters: dict {champ: valeur}. Combine en ET."""
        active = {k: v for k, v in filters.items() if v}
        if not active:
            return services
        out = []
        for svc in services:
            match = True
            for field, value in active.items():
                path = FILTERABLE_FIELDS.get(field)
                if not path:
                    continue
                if _get_path(svc, path) != value:
                    match = False
                    break
            if match:
                out.append(svc)
        return out

    def search_and_filter(self, query=None, filters=None):
        base = self.search(query) if query else self.get_all()
        return self.filter(base, filters or {})

    # ---------- CRUD d'écriture (V0.4) ----------

    @staticmethod
    def empty_skeleton():
        return {
            "identification": {
                "nom": None, "categorie": None, "proprietaire": None, "direction_beneficiaire": None,
                "date_creation": None, "statut_portfolio": None, "hebergement": None,
                "mode_developpement": None, "prestataire": None,
            },
            "proposition_valeur": {"objectif": None, "probleme_resolu": None, "benefices": None, "parties_prenantes": None},
            "description": {"fonctionnelle": None, "utilisateurs": None, "processus_supportes": None, "frequence_utilisation": None},
            "architecture": {"stack_technologique": None, "infrastructure": None, "donnees_traitees": None, "integrations": None},
            "securite": {"donnees_sensibles": None, "reglementation": None, "classification": None, "journalisation": None, "sauvegarde": None},
            "performance_sla": {"disponibilite_cible": None, "rto": None, "rpo": None, "support_horaire": None},
            "risques": {"risques_principaux": None, "impact_arret": None, "pca": None, "plan_mitigation": None},
            "cycle_vie": {"conception": None, "deploiement": None, "exploitation": None, "amelioration": None, "retrait": None},
            "notes": None,
            "meta": {"statut": None, "criticite": None, "completude_pct": 0},
        }

    @staticmethod
    def _deep_merge(target, payload):
        for key, value in payload.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                ServiceManager._deep_merge(target[key], value)
            else:
                target[key] = value
        return target

    def _generate_id(self, services):
        numbers = []
        for svc in services:
            m = re.match(r"APP-(\d+)$", svc.get("id", ""))
            if m:
                numbers.append(int(m.group(1)))
        next_n = (max(numbers) + 1) if numbers else 1
        return f"APP-{next_n:03d}"

    def _references(self, references_repository):
        return references_repository.read()

    def create(self, payload, references_repository=None):
        data = self.repository.read()
        services = data["services"]
        references = self._references(references_repository) if references_repository else {}

        requested_id = (payload.get("id") or "").strip() or None

        svc = self.empty_skeleton()
        svc = self._deep_merge(svc, payload)

        validate_service_record(svc, services, references, new_id=requested_id)

        svc["id"] = requested_id or self._generate_id(services)
        svc["meta"]["completude_pct"] = compute_completude_pct(svc)

        services.append(svc)
        data["services"] = services
        data["metadata"]["total_services"] = len(services)
        self.repository.write(data, backup=True)
        return svc

    def update(self, service_id, payload, references_repository=None):
        data = self.repository.read()
        services = data["services"]
        references = self._references(references_repository) if references_repository else {}

        existing = next((s for s in services if s["id"] == service_id), None)
        if existing is None:
            return None

        candidate = copy.deepcopy(existing)
        self._deep_merge(candidate, payload)

        validate_service_record(candidate, services, references, exclude_id=service_id)

        candidate["id"] = service_id
        candidate["meta"]["completude_pct"] = compute_completude_pct(candidate)

        idx = services.index(existing)
        services[idx] = candidate
        data["services"] = services
        self.repository.write(data, backup=True)
        return candidate

    def delete(self, service_id):
        data = self.repository.read()
        services = data["services"]
        remaining = [s for s in services if s["id"] != service_id]
        if len(remaining) == len(services):
            return False

        data["services"] = remaining
        data["metadata"]["total_services"] = len(remaining)
        self.repository.write(data, backup=True)
        return True
