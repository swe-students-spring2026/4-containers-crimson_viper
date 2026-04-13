from flask import Blueprint, request, jsonify
from services.entry_service import *

entry_bp = Blueprint("entries", __name__)

'''API routes for CRUD operations on entries DRAFT'''
@entry_bp.route("/entries", methods=["POST"])
def create():
    data = request.json
    username = data["username"]
    date = data["date"]
    entry_data = data["entry_data"]
    entry_id = create_entry(username, date, entry_data)
    return jsonify({"id": entry_id})

@entry_bp.route("/entries/<username>", methods=["GET"])
def get_all(username):
    return jsonify(get_all_entries(username))

@entry_bp.route("/entries/<username>/<date>", methods=["GET"])
def get_one(username, date):
    entry = get_entry_by_date(username, date)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)

@entry_bp.route("/entries/<username>/<date>/<int:entry_index>", methods=["PUT"])
def update(username, date, entry_index):
    updated_data = request.json
    update_entry(username, date, entry_index, updated_data)
    return jsonify({"msg": "updated"})

@entry_bp.route("/entries/<username>/<date>/<int:entry_index>", methods=["DELETE"])
def delete(username, date, entry_index):
    delete_entry(username, date, entry_index)
    return jsonify({"msg": "deleted"})