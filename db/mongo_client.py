# db/mongo_client.py

from pymongo import MongoClient
import os

# You can use .env MONGO_URI or fallback to localhost
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URI)
