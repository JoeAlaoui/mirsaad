import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("MIRSAAD_SECRET_KEY", "dev-secret-change-in-production")
    DEBUG = os.environ.get("MIRSAAD_DEBUG", "1") == "1"

    DATA_DIR = os.path.join(BASE_DIR, "data")
    SERVICES_FILE = os.path.join(DATA_DIR, "services.json")
    REFERENCES_FILE = os.path.join(DATA_DIR, "references.json")
    BACKUPS_DIR = os.path.join(DATA_DIR, "backups")

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 Mo, pour les futurs imports Excel
    ALLOWED_IMPORT_EXTENSIONS = {"xlsx"}

    APP_NAME = "MIRSAAD"
    APP_NAME_AR = "مرصاد"
    ORGANISATION = "AMMPS"
