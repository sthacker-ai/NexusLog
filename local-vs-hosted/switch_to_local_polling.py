"""
Delete Telegram Webhook — switch to local polling mode

Run this script when you want to develop locally with polling.
After running this, you can start the bot locally with:
    python telegram_bot.py

When you're done with local dev, re-set the webhook with:
    python set_telegram_webhook.py
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

def delete_webhook():
    # Load .env from project root
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    load_dotenv(dotenv_path=env_path)
    
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('nl_TELEGRAM_BOT_TOKEN') or os.getenv('NL_TELEGRAM_BOT_TOKEN')
    
    if not token:
        token = input("Enter your Telegram Bot Token: ").strip()
    
    print(f"Using Token: {token[:10]}...{token[-5:]}")
    print("Deleting webhook to switch to local polling mode...")
    
    api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    response = requests.post(api_url)
    
    if response.status_code == 200 and response.json().get('ok'):
        print("✅ Webhook deleted! You can now run the bot in polling mode:")
        print("   python telegram_bot.py")
        print()
        print("To switch back to Vercel webhook mode, run:")
        print("   python set_telegram_webhook.py")
    else:
        print("❌ Failed to delete webhook")
        print(response.text)

if __name__ == "__main__":
    delete_webhook()
