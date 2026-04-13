from models.db import entries_collection
from ml.summarizer import summarize

def create_entry(username, date, entry_data):
    """
    Adds a journal entry to the user's day document.
    If the day does not exist, this will create it.
    """
    entry_data["summary"] = summarize(entry_data.get("transcript", ""))
    result = entries_collection.update_one(
        {"username": username, "date": date},
        {"$push": {"journal_entries": entry_data}},
        upsert=True
    )
    return result.upserted_id or True

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
    return day

def update_entry(username, date, entry_index, updated_data):
    """
    Updates a specific journal entry in the day's journal_entries list.
    """
    key = f"journal_entries.{entry_index}"
    result = entries_collection.update_one(
        {"username": username, "date": date},
        {"$set": {key: updated_data}}
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