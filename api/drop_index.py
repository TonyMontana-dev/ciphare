from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB URI from environment
mongodb_uri = os.getenv('MONGODB_URI')
if not mongodb_uri:
    raise ValueError("MONGODB_URI environment variable is not set")

# Connect to MongoDB
client = MongoClient(mongodb_uri)
db = client.ciphare

# Drop the problematic index
try:
    db.posts.drop_index('post_id_1')
    print("Successfully dropped post_id_1 index")
except Exception as e:
    print(f"Error dropping index: {str(e)}")

client.close() 