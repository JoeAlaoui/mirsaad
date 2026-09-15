from flask import Blueprint, jsonify, current_app, request

from services.json_repository import JsonRepository
from services.service_manager import ServiceManager, FILTERABLE_FIELDS

bp = Blueprint("api_services", __name__, url_prefix="/api")


def _manager():
    repo = JsonRepository(current_app.config["SERVICES_FILE"], current_app.config["BACKUPS_DIR"])
    return ServiceManager(repo)


@bp.route("/services")
def list_services():
    manager = _manager()
    query = request.args.get("q", "").strip()
    filters = {field: request.args.get(field, "") for field in FILTERABLE_FIELDS}

    results = manager.search_and_filter(query=query, filters=filters)

    return jsonify({
        "services": results,
        "total": len(manager.get_all()),
        "nb_resultats": len(results),
        "query": query,
        "filters": filters,
    })


@bp.route("/services/<service_id>")
def get_service(service_id):
    manager = _manager()
    svc = manager.get_by_id(service_id)
    if not svc:
        return jsonify({"error": "Service introuvable", "id": service_id}), 404
    return jsonify(svc)


@bp.route("/references")
def references():
    repo = JsonRepository(current_app.config["REFERENCES_FILE"])
    return jsonify(repo.read())
