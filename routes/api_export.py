from datetime import datetime

from flask import Blueprint, current_app, send_file

from services.json_repository import JsonRepository
from services.statistics import compute_kpis
from services.excel_export import build_export_workbook

bp = Blueprint("api_export", __name__, url_prefix="/api/export")


@bp.route("/excel")
def export_excel():
    services_repo = JsonRepository(current_app.config["SERVICES_FILE"])
    services = services_repo.read()["services"]

    settings_repo = JsonRepository(current_app.config["SETTINGS_FILE"])
    settings = settings_repo.read()

    kpis = compute_kpis(services)

    buffer = build_export_workbook(
        services,
        kpis,
        organisation_name=settings.get("organisation_name", "Votre Organisation"),
        application_name=settings.get("application_name", "MIRSAAD"),
    )

    filename = f"portefeuille_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
