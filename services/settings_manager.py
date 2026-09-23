"""
Gestion des paramètres configurables de l'application (nom de l'organisation, seuils, etc.).
Toute donnée d'identité (nom d'agence) vit ici — jamais en dur dans le code ou les templates.
"""

ALLOWED_KEYS = {
    "organisation_name",
    "organisation_name_complete",
    "application_name",
    "application_name_ar",
    "seuil_completude_pct",
    "theme",
    "pdf_cover_mode",
    "pdf_footer_mode",
    "pdf_custom_text",
}

REQUIRED_KEYS = {"organisation_name", "application_name"}

ALLOWED_THEMES = {"institutionnel", "moderne", "ant"}
ALLOWED_PDF_COVER_MODES = {"logo", "texte"}
ALLOWED_PDF_FOOTER_MODES = {"vide", "personnalise"}


class SettingsValidationError(Exception):
    pass


def validate_settings(payload):
    """Valide un payload de mise à jour partielle des paramètres. Lève SettingsValidationError si invalide."""
    unknown = set(payload.keys()) - ALLOWED_KEYS
    if unknown:
        raise SettingsValidationError(f"Champs inconnus : {', '.join(sorted(unknown))}")

    if "organisation_name" in payload and not str(payload["organisation_name"]).strip():
        raise SettingsValidationError("Le nom de l'organisation ne peut pas être vide.")

    if "application_name" in payload and not str(payload["application_name"]).strip():
        raise SettingsValidationError("Le nom de l'application ne peut pas être vide.")

    if "seuil_completude_pct" in payload:
        try:
            v = int(payload["seuil_completude_pct"])
        except (TypeError, ValueError):
            raise SettingsValidationError("Le seuil de complétude doit être un entier.")
        if not (0 <= v <= 100):
            raise SettingsValidationError("Le seuil de complétude doit être compris entre 0 et 100.")

    if "theme" in payload and payload["theme"] not in ALLOWED_THEMES:
        raise SettingsValidationError(f"Thème inconnu : « {payload['theme']} » (valeurs autorisées : {', '.join(sorted(ALLOWED_THEMES))}).")

    if "pdf_cover_mode" in payload and payload["pdf_cover_mode"] not in ALLOWED_PDF_COVER_MODES:
        raise SettingsValidationError(f"Mode de page de garde inconnu : « {payload['pdf_cover_mode']} » (valeurs autorisées : {', '.join(sorted(ALLOWED_PDF_COVER_MODES))}).")

    if "pdf_footer_mode" in payload and payload["pdf_footer_mode"] not in ALLOWED_PDF_FOOTER_MODES:
        raise SettingsValidationError(f"Mode de pied de page inconnu : « {payload['pdf_footer_mode']} » (valeurs autorisées : {', '.join(sorted(ALLOWED_PDF_FOOTER_MODES))}).")

    return True


class SettingsManager:
    def __init__(self, repository):
        self.repository = repository

    def get(self):
        return self.repository.read()

    def update(self, payload):
        validate_settings(payload)
        current = self.repository.read()
        current.update(payload)
        self.repository.write(current, backup=True)
        return current
