import os
import uuid
import json

from flask import Blueprint, jsonify, current_app, request

from services.json_repository import JsonRepository
from services.import_export import parse_json, parse_excel, build_preview, apply_import, ImportError_

bp = Blueprint("api_import", __name__, url_prefix="/api/import")

IMPORTS_SUBDIR = "imports"


def _imports_dir():
    path = os.path.join(current_app.config["DATA_DIR"], IMPORTS_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


@bp.route("/preview", methods=["POST"])
def preview():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni (champ 'file' attendu)."}), 400

    file = request.files["file"]
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    allowed = current_app.config.get("ALLOWED_IMPORT_EXTENSIONS", {"json", "xlsx"})
    if ext not in allowed:
        return jsonify({"error": f"Format non supporté. Utilisez un fichier .{' ou .'.join(sorted(allowed))}."}), 400

    file_bytes = file.read()

    try:
        if ext == "json":
            imported, errors = parse_json(file_bytes)
        else:
            imported, errors = parse_excel(file_bytes)
    except ImportError_ as e:
        return jsonify({"error": str(e)}), 400

    repo = JsonRepository(current_app.config["SERVICES_FILE"])
    existing = repo.read()["services"]

    preview_data = build_preview(existing, imported, errors)

    token = uuid.uuid4().hex
    token_path = os.path.join(_imports_dir(), f"{token}.json")
    with open(token_path, "w", encoding="utf-8") as f:
        json.dump(imported, f, ensure_ascii=False)

    return jsonify({"token": token, "preview": preview_data})


@bp.route("/confirm", methods=["POST"])
def confirm():
    payload = request.get_json(silent=True) or {}
    token = payload.get("token")
    strategy = payload.get("strategy")

    if not token or strategy not in ("remplacer", "ajouter", "maj"):
        return jsonify({"error": "Requête invalide : 'token' et 'strategy' (remplacer/ajouter/maj) requis."}), 400

    token_path = os.path.join(_imports_dir(), f"{token}.json")
    if not os.path.exists(token_path):
        return jsonify({"error": "Session d'import expirée ou introuvable. Relancez l'import."}), 404

    with open(token_path, encoding="utf-8") as f:
        imported = json.load(f)

    repo = JsonRepository(current_app.config["SERVICES_FILE"], current_app.config["BACKUPS_DIR"])
    data = repo.read()

    try:
        new_services = apply_import(data["services"], imported, strategy)
    except ImportError_ as e:
        return jsonify({"error": str(e)}), 400

    data["services"] = new_services
    data["metadata"]["total_services"] = len(new_services)
    repo.write(data, backup=True)

    os.remove(token_path)

    return jsonify({"total_services": len(new_services), "strategy": strategy})
