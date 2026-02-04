import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

url = os.getenv('DATABASE_URL')

if not url:
    print("❌ Error: DATABASE_URL not found in .env")
    exit(1)

print(f"Attempting to connect...")

try:
    # Create engine and connect
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("\n✅ SUCCESS! Connection to database established.")
        print("The connection string is valid.")
except Exception as e:
    print("\n❌ FAILURE: Could not connect.")
    print(f"Error details: {str(e)}")
    
    if "password authentication failed" in str(e).lower():
        print("\n💡 Tip: Check your password. If it has special characters like '@', make sure they are URL encoded (e.g., '@' becomes '%40').")
    elif "does not exist" in str(e).lower():
        print("\n💡 Tip: The database 'nexuslog' might not exist. Did you run the CREATE DATABASE sql command?")
