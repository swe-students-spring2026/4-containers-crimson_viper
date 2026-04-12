from flask import Blueprint, request, jsonify
from services.entry_service import *

entry_bp = Blueprint("entries", __name__)

'''API routes for CRUD operations on entries DRAFT'''
@entry_bp.route("/entries", methods=["POST"])
def create():
    data = request.json
    entry_id = create_entry(data)
    return jsonify({"id": entry_id})

@entry_bp.route("/entries", methods=["GET"])
def get_all():
    return jsonify(get_all_entries())

@entry_bp.route("/entries/<date>", methods=["GET"])
def get_one(date):
    entry = get_entry_by_date(date)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)

@entry_bp.route("/entries/<date>", methods=["PUT"])
def update(date):
    data = request.json
    update_entry(date, data)
    return jsonify({"msg": "updated"})

@entry_bp.route("/entries/<date>", methods=["DELETE"])
def delete(date):
    delete_entry(date)
    return jsonify({"msg": "deleted"})