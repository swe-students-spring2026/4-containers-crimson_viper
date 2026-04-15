from datetime import datetime
from uuid import uuid4

from models.db import entries_collection
# from ml.summarizer import summarize

def create_entry(username, date, entry_data):
    entry_data = dict(entry_data)
    entry_data["entry_id"] = entry_data.get("entry_id") or str(uuid4())
    entry_data["created_at"] = entry_data.get("created_at") or datetime.utcnow().isoformat()
    # entry_data["summary"] = summarize(entry_data.get("transcript", ""))

    result = entries_collection.update_one(
        {"username": username, "date": date},
        {
            "$setOnInsert": {
                "username": username,
                "date": date,
            },
            "$push": {"journal_entries": entry_data},
        },
        upsert=True,
    )

    if result.modified_count or result.upserted_id:
        return True
    return False


def get_all_entries(username):
    """
    Returns all day documents for a specified user.
    """
    days = list(entries_collection.find({"username": username}))
    for day in days:
        day["_id"] = str(day["_id"])
    return days

def get_entry_by_date(username, date):
    """
    Returns the day document for a user and date.
    """
    day = entries_collection.find_one({"username": username, "date": date})
    if day:
        day["_id"] = str(day["_id"])
        day.setdefault("journal_entries", [])
        day.setdefault("tasks", [])
        day["journal_entries"] = sorted(
            day["journal_entries"],
            key=lambda entry: entry.get("created_at") or entry.get("timestamp") or ""
        )
    return day

def update_entry(username, date, entry_index, updated_data):
    """
    Updates a specific journal entry in the day's journal_entries list.
    """
    day = entries_collection.find_one({"username": username, "date": date})
    if not day or "journal_entries" not in day or entry_index >= len(day["journal_entries"]):
        return 0

    existing_entry = day["journal_entries"][entry_index]
    merged_entry = {**existing_entry, **updated_data}
    # merged_entry["summary"] = summarize(merged_entry.get("transcript", ""))

    key = f"journal_entries.{entry_index}"
    result = entries_collection.update_one(
        {"username": username, "date": date},
        {"$set": {key: merged_entry}}
    )
    return result.modified_count

def delete_entry(username, date, entry_index):
    """
    Deletes a specific journal entry from the day's journal_entries list.
    """
    day = entries_collection.find_one({"username": username, "date": date})
    if not day or "journal_entries" not in day or entry_index >= len(day["journal_entries"]):
        return 0
    entries = day["journal_entries"]
    entries.pop(entry_index)
    result = entries_collection.update_one(
        {"username": username, "date": date},
        {"$set": {"journal_entries": entries}}
    )
    return result.modified_count

def add_task(username, date, task_data):
    """
    Adds a task to the day's tasks list for the user.
    """
    day = entries_collection.find_one({"username": username, "date": date})
    if day:
        result = entries_collection.update_one(
            {"username": username, "date": date},
            {"$push": {"tasks": task_data}}
        )
        return result.modified_count
    else:
        result = entries_collection.update_one(
            {"username": username, "date": date},
            {
                "$set": {
                    "username": username,
                    "date": date,
                    "tasks": [task_data],
                }
            },
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        return True
    
def edit_task(username, date, task_index, updated_task):
    """
    Updates a specific task in the day's tasks list.
    """
    key = f"tasks.{task_index}"
    result = entries_collection.update_one(
        {"username": username, "date": date},
        {"$set": {key: updated_task}}
    )
    return result.modified_count
    

def delete_task(username, date, task_index):
    """
    Deletes a specific task from the day's tasks list.
    """
    day = entries_collection.find_one({"username": username, "date": date})
    if not day or "tasks" not in day or task_index >= len(day["tasks"]):
        return 0
    tasks = day["tasks"]
    tasks.pop(task_index)
    result = entries_collection.update_one(
        {"username": username, "date": date},
        {"$set": {"tasks": tasks}}
    )
    return result.modified_count