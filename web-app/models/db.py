"""
Connects to database
"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["diary_db"]
entries_collection = db["entries"]
