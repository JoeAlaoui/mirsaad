"""
Validation des services pour la création/modification (CRUD, V0.4).
Détecte : champs obligatoires manquants, ID en doublon, nom en doublon, valeurs hors référentiel.
"""

REQUIRED_FIELDS = [
    (("identification", "nom"), "Le nom du service est obligatoire."),
]

# Champs dont la valeur, si fournie, doit appartenir au référentiel correspondant.
CONTROLLED_FIELDS = {
    ("identification", "statut_portfolio"): "statut_portfolio",
    ("identification", "hebergement"): "hebergement",
    ("identification", "mode_developpement"): "mode_developpement",
    ("identification", "categorie"): "categorie",
    ("meta", "criticite"): "criticite",
    ("meta", "statut"): "statut",
}


class ServiceValidationError(Exception):
    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


def _get_path(d, path):
    v = d
    for key in path:
        if not isinstance(v, dict):
            return None
        v = v.get(key)
    return v


def _allowed_values(references, ref_key):
    entry = references.get(ref_key)
    if entry is None:
        return None
    if isinstance(entry, dict) and "values" in entry:
        return entry["values"]
    if isinstance(entry, list):
        return entry
    return None


def validate_required_fields(payload):
    for path, message in REQUIRED_FIELDS:
        value = _get_path(payload, path)
        if not value or not str(value).strip():
            raise ServiceValidationError(message, field=".".join(path))


def validate_controlled_values(payload, references):
    for path, ref_key in CONTROLLED_FIELDS.items():
        value = _get_path(payload, path)
        if not value:
            continue
        allowed = _allowed_values(references, ref_key)
        if allowed and value not in allowed:
            raise ServiceValidationError(
                f"Valeur non reconnue pour {'.'.join(path)} : « {value} » "
                f"(valeurs autorisées : {', '.join(str(a) for a in allowed)}).",
                field=".".join(path),
            )


def validate_no_duplicate_id(new_id, existing_services, exclude_id=None):
    for svc in existing_services:
        if svc["id"] == exclude_id:
            continue
        if svc["id"] == new_id:
            raise ServiceValidationError(f"L'identifiant « {new_id} » est déjà utilisé.", field="id")


def validate_no_duplicate_name(nom, existing_services, exclude_id=None):
    nom_norm = str(nom).strip().lower()
    for svc in existing_services:
        if svc["id"] == exclude_id:
            continue
        existing_nom = (svc.get("identification", {}) or {}).get("nom", "")
        if str(existing_nom).strip().lower() == nom_norm:
            raise ServiceValidationError(f"Un service nommé « {nom} » existe déjà ({svc['id']}).", field="identification.nom")


def validate_service_record(merged_record, existing_services, references, exclude_id=None, new_id=None):
    """Valide l'état final d'un service après fusion payload + existant (create ou update)."""
    validate_required_fields(merged_record)
    validate_controlled_values(merged_record, references)

    nom = _get_path(merged_record, ("identification", "nom"))
    if nom:
        validate_no_duplicate_name(nom, existing_services, exclude_id=exclude_id)

    if new_id:
        validate_no_duplicate_id(new_id, existing_services, exclude_id=exclude_id)
