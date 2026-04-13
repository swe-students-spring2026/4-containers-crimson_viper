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
    # Convert ObjectId to string if necessary
    if hasattr(entry_id, "__str__") and not isinstance(entry_id, (bool, int, str)):
        entry_id = str(entry_id)
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

@entry_bp.route("/tasks/<username>/<date>", methods=["POST"])
def create_task(username, date):
    task_data = request.json
    result = add_task(username, date, task_data)
    return jsonify({"result": result})

@entry_bp.route("/tasks/<username>/<date>/<int:task_index>", methods=["PUT"])
def update_task(username, date, task_index):
    updated_task = request.json
    result = edit_task(username, date, task_index, updated_task)
    return jsonify({"result": result})

@entry_bp.route("/tasks/<username>/<date>/<int:task_index>", methods=["DELETE"])
def remove_task(username, date, task_index):
    result = delete_task(username, date, task_index)
    return jsonify({"result": result})

@entry_bp.route("/tasks/<username>/<date>", methods=["POST"])
def create_task_route(username, date):
    task_data = request.json
    result = add_task(username, date, task_data)
    return jsonify({"msg": "task added", "result": str(result)})

@entry_bp.route("/tasks/<username>/<date>/<int:task_index>", methods=["PUT"])
def update_task_route(username, date, task_index):
    updated_task = request.json
    result = edit_task(username, date, task_index, updated_task)
    if not result:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"msg": "task updated"})

@entry_bp.route("/tasks/<username>/<date>/<int:task_index>", methods=["DELETE"])
def delete_task_route(username, date, task_index):
    result = delete_task(username, date, task_index)
    if not result:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"msg": "task deleted"})