from flask import Blueprint, jsonify, current_app

from services.json_repository import JsonRepository
from services.statistics import compute_kpis
from services.quality import quality_report

bp = Blueprint("api_dashboard", __name__, url_prefix="/api")


@bp.route("/dashboard")
def dashboard():
    repo = JsonRepository(current_app.config["SERVICES_FILE"], current_app.config["BACKUPS_DIR"])
    data = repo.read()
    services = data["services"]

    return jsonify({
        "metadata": data["metadata"],
        "kpis": compute_kpis(services),
        "quality": quality_report(services),
    })
