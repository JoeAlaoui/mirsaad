from flask import Blueprint, current_app, send_file, jsonify
import io

from services.json_repository import JsonRepository
from services.service_manager import ServiceManager
from services.statistics import compute_kpis
from services.quality import quality_report
from services.pdf_service import generate_full_report, generate_service_report

bp = Blueprint("api_reports", __name__, url_prefix="/api/reports")


def _settings():
    return JsonRepository(current_app.config["SETTINGS_FILE"]).read()


@bp.route("/pdf")
def full_report():
    repo = JsonRepository(current_app.config["SERVICES_FILE"], current_app.config["BACKUPS_DIR"])
    data = repo.read()
    services = data["services"]

    kpis = compute_kpis(services)
    quality = quality_report(services)
    settings = _settings()

    pdf_bytes = generate_full_report(services, kpis, quality, settings)

    filename = f"{settings.get('application_name', 'MIRSAAD').lower()}_rapport_portefeuille.pdf"
    return send_file(io.BytesIO(pdf_bytes), as_attachment=True, download_name=filename, mimetype="application/pdf")


@bp.route("/pdf/<service_id>")
def service_report(service_id):
    repo = JsonRepository(current_app.config["SERVICES_FILE"], current_app.config["BACKUPS_DIR"])
    manager = ServiceManager(repo)
    svc = manager.get_by_id(service_id)
    if not svc:
        return jsonify({"error": "Service introuvable", "id": service_id}), 404

    settings = _settings()
    pdf_bytes = generate_service_report(svc, settings)

    filename = f"fiche_{service_id}.pdf"
    return send_file(io.BytesIO(pdf_bytes), as_attachment=True, download_name=filename, mimetype="application/pdf")
