from flask import Blueprint, jsonify, current_app, request

from services.json_repository import JsonRepository
from services.service_manager import ServiceManager, FILTERABLE_FIELDS
from services.validation import ServiceValidationError

bp = Blueprint("api_services", __name__, url_prefix="/api")


def _manager():
    repo = JsonRepository(current_app.config["SERVICES_FILE"], current_app.config["BACKUPS_DIR"])
    return ServiceManager(repo)


def _references_repo():
    return JsonRepository(current_app.config["REFERENCES_FILE"])


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


@bp.route("/services", methods=["POST"])
def create_service():
    payload = request.get_json(silent=True) or {}
    manager = _manager()
    try:
        svc = manager.create(payload, references_repository=_references_repo())
    except ServiceValidationError as e:
        return jsonify({"error": str(e), "field": e.field}), 400
    return jsonify(svc), 201


@bp.route("/services/<service_id>", methods=["PUT"])
def update_service(service_id):
    payload = request.get_json(silent=True) or {}
    manager = _manager()
    try:
        svc = manager.update(service_id, payload, references_repository=_references_repo())
    except ServiceValidationError as e:
        return jsonify({"error": str(e), "field": e.field}), 400
    if svc is None:
        return jsonify({"error": "Service introuvable", "id": service_id}), 404
    return jsonify(svc)


@bp.route("/services/<service_id>", methods=["DELETE"])
def delete_service(service_id):
    manager = _manager()
    deleted = manager.delete(service_id)
    if not deleted:
        return jsonify({"error": "Service introuvable", "id": service_id}), 404
    return jsonify({"deleted": True, "id": service_id})


@bp.route("/references")
def references():
    return jsonify(_references_repo().read())
