"""
Logique métier sur les services : accès, recherche, filtres.
CRUD d'écriture (add/update/delete) prévu pour V0.4 — lecture seule pour le socle V0.2/V0.3.
"""

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
