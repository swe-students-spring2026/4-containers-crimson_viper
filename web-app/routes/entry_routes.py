"""
App routes
"""

from flask import Blueprint, request, jsonify
from services.entry_service import (
    add_task,
    create_entry,
    delete_entry,
    delete_task,
    edit_task,
    get_all_entries,
    get_entry_by_date,
    update_entry,
)

entry_bp = Blueprint("entries", __name__)


@entry_bp.route("/entries", methods=["POST"])
def create():
    """
    Creates a new entry
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    date = data.get("date")
    entry_data = data.get("entry_data")

    if not username or not date or not isinstance(entry_data, dict):
        return jsonify({"error": "username, date, and entry_data are required"}), 400

    entry_id = create_entry(username, date, entry_data)
    if hasattr(entry_id, "__str__") and not isinstance(entry_id, (bool, int, str)):
        entry_id = str(entry_id)
    return jsonify({"id": entry_id})


@entry_bp.route("/entries/<username>", methods=["GET"])
def get_all(username):
    """
    Gets all usernames
    """
    return jsonify(get_all_entries(username))


@entry_bp.route("/entries/<username>/<date>", methods=["GET"])
def get_one(username, date):
    """
    Gets one entry with username and date
    """
    entry = get_entry_by_date(username, date)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)


@entry_bp.route("/entries/<username>/<date>/<int:entry_index>", methods=["PUT"])
def update(username, date, entry_index):
    """
    Updates an entry
    """
    updated_data = request.get_json(silent=True) or {}
    result = update_entry(username, date, entry_index, updated_data)
    if not result:
        return jsonify({"error": "Entry not found"}), 404
    return jsonify({"msg": "updated"})


@entry_bp.route("/entries/<username>/<date>/<int:entry_index>", methods=["DELETE"])
def delete(username, date, entry_index):
    """
    Deletes an entry
    """
    result = delete_entry(username, date, entry_index)
    if not result:
        return jsonify({"error": "Entry not found"}), 404
    return jsonify({"msg": "deleted"})


@entry_bp.route("/tasks/<username>/<date>", methods=["POST"])
def create_task(username, date):
    """
    Creates a new task
    """
    task_data = request.get_json(silent=True) or {}
    result = add_task(username, date, task_data)
    return jsonify({"msg": "task added", "result": str(result)})


@entry_bp.route("/tasks/<username>/<date>/<int:task_index>", methods=["PUT"])
def update_task(username, date, task_index):
    """
    Updates a task
    """
    updated_task = request.get_json(silent=True) or {}
    result = edit_task(username, date, task_index, updated_task)
    if not result:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"msg": "task updated"})


@entry_bp.route("/tasks/<username>/<date>/<int:task_index>", methods=["DELETE"])
def remove_task(username, date, task_index):
    """
    Removes a task
    """
    result = delete_task(username, date, task_index)
    if not result:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"msg": "task deleted"})
