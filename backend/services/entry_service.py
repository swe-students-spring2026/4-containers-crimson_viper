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

def get_entry_by_date(date):
    entry = entries_collection.find_one({"date": date})
    if entry:
        entry["_id"] = str(entry["_id"])
    return entry

def update_entry(date, data):
    return entries_collection.update_one(
        {"date": date},
        {"$set": data}
    )

def delete_entry(date):
    return entries_collection.delete_one({"date": date})