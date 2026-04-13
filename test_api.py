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

# 6. ADD a task
task_data = {
    "title": "Finish backend routes",
    "deadline": "2026-04-12 23:59",
    "done": False
}
requests.post(f"{BASE}/tasks/{USERNAME}/{DATE}", json=task_data)

print("\nUser entry after adding task:")
res = requests.get(f"{BASE}/entries/{USERNAME}/{DATE}")
print(res.json())

# 7. UPDATE task at index 0
updated_task = {
    "title": "Finish backend routes and test them",
    "deadline": "2026-04-12 23:59",
    "done": True
}
requests.put(f"{BASE}/tasks/{USERNAME}/{DATE}/0", json=updated_task)

print("\nUser entry after updating task:")
res = requests.get(f"{BASE}/entries/{USERNAME}/{DATE}")
print(res.json())

# 8. DELETE task at index 0
requests.delete(f"{BASE}/tasks/{USERNAME}/{DATE}/0")

print("\nUser entry after deleting task:")
res = requests.get(f"{BASE}/entries/{USERNAME}/{DATE}")
print(res.json())