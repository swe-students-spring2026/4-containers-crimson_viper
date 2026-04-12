from models.db import entries_collection
from ml.summarizer import summarize

def create_entry(data):
    data["summary"] = summarize(data.get("transcript", ""))
    result = entries_collection.insert_one(data)
    return str(result.inserted_id)

def get_all_entries():
    entries = list(entries_collection.find())
    for e in entries:
        e["_id"] = str(e["_id"])
    return entries

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