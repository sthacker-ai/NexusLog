import os
import requests
from dotenv import load_dotenv

def set_webhook():
    # Load env vars
    load_dotenv()
    
    # Try to get token from env
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('nl_TELEGRAM_BOT_TOKEN') or os.getenv('NL_TELEGRAM_BOT_TOKEN')
    
    if not token:
        token = input("Enter your Telegram Bot Token: ").strip()
    
    print(f"Using Token: {token[:10]}...{token[-5:]}")
    
    # Get deployment URL
    base_url = input("Enter your Vercel Deployment URL (e.g. https://nexuslog.vercel.app): ").strip()
    
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    webhook_url = f"{base_url}/api/telegram-webhook"
    
    print(f"Setting webhook to: {webhook_url}")
    
    # Call Telegram API
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    response = requests.post(api_url, data={'url': webhook_url})
    
    if response.status_code == 200:
        print("✅ Webhook set successfully!")
        print(response.json())
    else:
        print("❌ Failed to set webhook")
        print(response.text)

if __name__ == "__main__":
    set_webhook()
