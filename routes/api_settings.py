from flask import Blueprint, jsonify, current_app, request

from services.json_repository import JsonRepository
from services.settings_manager import SettingsManager, SettingsValidationError

bp = Blueprint("api_settings", __name__, url_prefix="/api")


def _manager():
    repo = JsonRepository(current_app.config["SETTINGS_FILE"], current_app.config["BACKUPS_DIR"])
    return SettingsManager(repo)


@bp.route("/settings", methods=["GET"])
def get_settings():
    return jsonify(_manager().get())


@bp.route("/settings", methods=["PUT"])
def update_settings():
    payload = request.get_json(silent=True) or {}
    try:
        updated = _manager().update(payload)
    except SettingsValidationError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(updated)
