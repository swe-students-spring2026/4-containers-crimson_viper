import requests

BASE = "http://127.0.0.1:5000"
USERNAME = "testuser"
DATE = "2026-04-12"

# 1. CREATE entry
print("Creating entry...")
entry_data = {
    "transcript": "Today I worked on my project",
    "mood": "productive",
    "timestamp": "2026-04-12T09:00:00"
}
res = requests.post(f"{BASE}/entries", json={
    "username": USERNAME,
    "date": DATE,
    "entry_data": entry_data
})
print(res.json())

# 2. GET all entries for the user
print("\nGetting all entries for user...")
res = requests.get(f"{BASE}/entries/{USERNAME}")
print(res.json())

# 3. GET one day's entry
print("\nGetting one day's entry...")
res = requests.get(f"{BASE}/entries/{USERNAME}/{DATE}")
print(res.json())

# 4. UPDATE the first journal entry (index 0)
print("\nUpdating entry...")
updated_entry = {
    "transcript": "Updated transcript",
    "mood": "very productive",
    "timestamp": "2026-04-12T09:00:00"
}
res = requests.put(f"{BASE}/entries/{USERNAME}/{DATE}/0", json=updated_entry)
print(res.json())

# 5. DELETE the first journal entry (index 0)
print("\nDeleting entry...")
res = requests.delete(f"{BASE}/entries/{USERNAME}/{DATE}/0")
print(res.json())