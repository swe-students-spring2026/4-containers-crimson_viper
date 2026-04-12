import requests

BASE = "http://127.0.0.1:5000"

# 1. CREATE entry
print("Creating entry...")
res = requests.post(f"{BASE}/entries", json={
    "date": "2026-04-12",
    "transcript": "Today I worked on my project",
    "mood": "productive"
})
print(res.json())


# 2. GET all entries
print("\nGetting all entries...")
res = requests.get(f"{BASE}/entries")
print(res.json())


# 3. GET one entry
print("\nGetting one entry...")
res = requests.get(f"{BASE}/entries/2026-04-12")
print(res.json())


# 4. UPDATE entry
print("\nUpdating entry...")
res = requests.put(f"{BASE}/entries/2026-04-12", json={
    "mood": "very productive"
})
print(res.json())


# 5. DELETE entry
print("\nDeleting entry...")
res = requests.delete(f"{BASE}/entries/2026-04-12")
print(res.json())