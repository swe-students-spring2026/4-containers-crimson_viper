"""
Connects to database
"""

import os
from pymongo import MongoClient

# we need to make sure that the database is connected correctly with the
# MongoDB database in the container
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)

db_name = os.getenv("DB_NAME", "crimson_viper")
db = client[db_name]

users_collection = db["users"]
entries_collection = db["entries"]
audio_jobs_collection = db["audio_jobs"]
