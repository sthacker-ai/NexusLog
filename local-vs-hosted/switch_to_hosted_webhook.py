"""
Switch to Hosted Webhook Mode (Vercel)

Run this script to configure your Telegram Bot to send updates to your Vercel deployment.
This disables local polling.

After running this, your bot will work on Vercel.
To switch back to local development, use:
    python switch_to_local_polling.py
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

def set_hosted_webhook():
    # Load .env from project root
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Try to get token from env
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('nl_TELEGRAM_BOT_TOKEN') or os.getenv('NL_TELEGRAM_BOT_TOKEN')
    
    if not token:
        token = input("Enter your Telegram Bot Token: ").strip()
    
    print(f"Using Token: {token[:10]}...{token[-5:]}")
    
    # Get deployment URL
    default_url = "https://nexuslog.vercel.app"
    base_url = input(f"Enter your Vercel Deployment URL (default: {default_url}): ").strip()
    
    if not base_url:
        base_url = default_url
    
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    webhook_url = f"{base_url}/api/telegram-webhook"
    
    print(f"Setting webhook to: {webhook_url}")
    
    # Call Telegram API
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    try:
        response = requests.post(api_url, data={'url': webhook_url}, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            print("✅ Webhook set successfully!")
            print(f"   Bot is now active on Vercel: {base_url}")
            print("   Local polling is disabled.")
        else:
            print("❌ Failed to set webhook")
            print(response.text)
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")

if __name__ == "__main__":
    set_hosted_webhook()
