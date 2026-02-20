import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.environ.get('MONGO_URI')
print(f"Testing connection to: {uri.split('@')[-1] if uri else 'None'}")

if not uri:
    print("❌ Error: MONGO_URI not found in .env file")
    exit(1)

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # The 'ping' command is cheap and does not require auth
    client.admin.command('ping')
    print("✅ Success: Connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nTroubleshooting Tips:")
    print("1. Whitelist your current IP address in MongoDB Atlas (Network Access).")
    print("2. Ensure username 'vhari032007_db_user' and password are correct.")
    print("3. Check if your ISP or Firewall is blocking port 27017.")
