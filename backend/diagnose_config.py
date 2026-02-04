import os
import sys
from dotenv import load_dotenv

# Try to find .env logic similar to what we suspect is needed
current_dir = os.getcwd()
print(f"Current Working Directory: {current_dir}")

# Attempt generic load
load_dotenv()

print("--- Environment Check ---")
print(f"TELEGRAM_BOT_TOKEN: {'SET' if os.getenv('TELEGRAM_BOT_TOKEN') else 'MISSING'}")
print(f"GOOGLE_AI_API_KEY: {'SET' if os.getenv('GOOGLE_AI_API_KEY') else 'MISSING'}")
print(f"REPLICATE_API_KEY: {'SET' if os.getenv('REPLICATE_API_KEY') else 'MISSING'}")

# Explicit parent check
parent_env = os.path.join(os.path.dirname(current_dir), '.env')
print(f"Checking parent .env at: {parent_env}")
if os.path.exists(parent_env):
    print("Parent .env exists.")
else:
    print("Parent .env NOT found.")
