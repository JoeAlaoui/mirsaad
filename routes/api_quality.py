from flask import Blueprint, jsonify, current_app, request

from services.json_repository import JsonRepository
from services.quality import quality_report

bp = Blueprint("api_quality", __name__, url_prefix="/api")


def _seuil():
    repo = JsonRepository(current_app.config["SETTINGS_FILE"])
    return repo.read().get("seuil_completude_pct", 70)


@bp.route("/quality")
def quality():
    repo = JsonRepository(current_app.config["SERVICES_FILE"], current_app.config["BACKUPS_DIR"])
    data = repo.read()
    services = data["services"]
    report = quality_report(services, seuil_pct=_seuil())

    anomalie = request.args.get("anomalie")
    services_concernes = None
    if anomalie and anomalie in report["anomalies"]:
        ids = set(report["anomalies"][anomalie])
        services_concernes = [s for s in services if s["id"] in ids]

    return jsonify({
        "report": report,
        "anomalie_filtre": anomalie,
        "services_filtres": services_concernes,
    })
