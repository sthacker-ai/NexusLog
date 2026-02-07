# 🧠 NexusLog - Setup Guide

Welcome to **NexusLog** - Your Neural Nexus for Ideas!

This guide will walk you through setting up NexusLog from scratch.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** (for backend)
- **Node.js 18+** and **npm** (for frontend)
- **PostgreSQL 14+** (database)
- **Ollama** (optional, for local AI processing)

---

## 🗄️ Step 1: PostgreSQL Database Setup

### 1.1 Create Database

Open your PostgreSQL client (pgAdmin, psql, or any tool) and run:

```sql
CREATE DATABASE nexuslog;
```

### 1.2 Create User (Optional but Recommended)

```sql
CREATE USER nexuslog_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE nexuslog TO nexuslog_user;
```

### 1.3 Initialize Schema

Navigate to the project directory and run the initialization script:

```bash
psql -U nexuslog_user -d nexuslog -f database/init_db.sql
```

Or if using default postgres user:

```bash
psql -U postgres -d nexuslog -f database/init_db.sql
```

✅ **Verify**: You should see tables created: `categories`, `entries`, `content_ideas`, `projects`, `config`

---

## 🤖 Step 2: Telegram Bot Setup

### 2.1 Create Bot via BotFather

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the prompts:
   - **Bot name**: NexusLog (or any name you prefer)
   - **Bot username**: Must end with "bot" (e.g., `mynexuslog_bot`)
4. **Save the bot token** - you'll need this!

### 2.2 Set Webhook (For Production Only)

For local development, we'll use polling mode (no webhook needed).

For production deployment, you'll set the webhook URL later.

---

## 🔑 Step 3: API Keys Setup

### 3.1 Google Gemini API Key

You mentioned you already have this! If not:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Save it securely

### 3.2 Ollama Setup (Local AI)

If you have Ollama installed:

```bash
# Pull a model (if not already done)
ollama pull llama2
```

Verify it's running:
```bash
curl http://localhost:11434/api/generate -d '{"model": "llama2", "prompt": "test"}'
```

### 3.3 Replicate API Key (Optional Fallback)

If you want to use Replicate as fallback:

1. Go to [Replicate](https://replicate.com)
2. Sign in and get your API token
3. Save it

### 3.4 Google Sheets Credentials

You mentioned you already have these! Place your credentials file at:

```
credentials/google-sheets-creds.json
```

Also, get your Google Sheet ID from the URL:
```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
```

---

## ⚙️ Step 4: Environment Configuration

### 4.1 Create .env File

Copy the template:

```bash
copy .env.template .env
```

### 4.2 Edit .env File

Open `.env` and fill in your values:

```env
# Database
DATABASE_URL=postgresql://nexuslog_user:your_secure_password@localhost:5432/nexuslog

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz  # From BotFather
TELEGRAM_WEBHOOK_URL=  # Leave empty for local development

# AI Services
GOOGLE_AI_API_KEY=your_gemini_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
REPLICATE_API_KEY=  # Optional
OPENAI_API_KEY=  # Optional

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials/google-sheets-creds.json
GOOGLE_SHEET_ID=your_sheet_id_here

# Flask
FLASK_SECRET_KEY=generate_a_random_secret_key_here
FLASK_ENV=development

# Deployment
DEPLOYMENT_TARGET=local  # Change to 'hostinger' or 'vercel' for production
CUSTOM_DOMAIN=thinkbits.in/nexuslog

# TTS
DEFAULT_TTS_VOICE=en-GB-male
TTS_PROVIDER=gemini
```

**Important**: Generate a secure Flask secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🐍 Step 5: Backend Setup

### 5.1 Create Virtual Environment

```bash
cd backend
python -m venv venv
```

### 5.2 Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 5.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 5.4 Test Backend

```bash
python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

✅ **Verify**: Visit `http://localhost:5000/api/health` - you should see `{"status": "healthy"}`

---

## 🎨 Step 6: Frontend Setup

### 6.1 Install Dependencies

```bash
cd frontend
npm install
```

### 6.2 Run Development Server

```bash
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
```

✅ **Verify**: Visit `http://localhost:3000` - you should see the NexusLog dashboard!

---

## 🤖 Step 7: Start Telegram Bot

In a **new terminal** (keep backend and frontend running):

```bash
cd backend
python telegram_bot.py
```

You should see:
```
🤖 NexusLog Telegram Bot is running...
```

✅ **Verify**: Send a message to your bot on Telegram - it should respond!

---

## 🧪 Step 8: Test the System

### 8.1 Test via Telegram

1. Open your bot in Telegram
2. Send `/start`
3. Send a text message: "content idea for blog: How to build AI apps"
4. Check the web UI - you should see the entry!

### 8.2 Test via Web UI

1. Go to `http://localhost:3000/add`
2. Fill in the form
3. Click "Create Entry"
4. Check Dashboard - entry should appear!

### 8.3 Test AI Categorization

1. Add an entry with "Use AI to validate" checked
2. The AI should automatically categorize it

---

## 🚀 Step 9: Deployment (Optional)

### Option A: Vercel Deployment

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Deploy frontend:
```bash
cd frontend
vercel
```

3. For backend, use Vercel serverless functions or deploy to a separate service

### Option B: Hostinger Deployment (thinkbits.in/nexuslog)

1. **Backend**: Deploy Flask app to Hostinger using their Python hosting
   - Upload backend files
   - Set environment variables in Hostinger control panel
   - Configure WSGI

2. **Frontend**: Build and upload
```bash
cd frontend
npm run build
# Upload dist/ folder to public_html/nexuslog/
```

3. **Database**: Use Hostinger's PostgreSQL or external PostgreSQL service

4. **Telegram Webhook**: Update webhook URL
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://thinkbits.in/nexuslog/api/telegram/webhook"
```

---

## 📱 Step 10: PWA Installation (Mobile)

1. Open `http://localhost:3000` (or your deployed URL) on your phone
2. Browser menu → "Add to Home Screen"
3. The app will install like a native app!

---

## 🔧 Troubleshooting

### Database Connection Error

- Verify PostgreSQL is running: `pg_ctl status`
- Check DATABASE_URL in .env
- Ensure database exists: `psql -l`

### Telegram Bot Not Responding

- Verify bot token is correct
- Check if telegram_bot.py is running
- Look for errors in terminal

### AI Services Not Working

- **Gemini**: Verify API key is valid
- **Ollama**: Check if Ollama is running: `curl http://localhost:11434`
- Check backend logs for errors

### Frontend Not Loading

- Ensure backend is running on port 5000
- Check browser console for errors
- Verify API proxy in vite.config.js

---

## 🔒 Security Best Practices

NexusLog follows strict security guidelines:

### Required
- **All secrets in `.env`** - Never commit API keys or tokens
- **Local fonts only** - No CDN dependencies (uses @fontsource)
- **Token redaction** - Sensitive data hidden in log displays

### Included by Default
- `.env` is in `.gitignore`
- React event handlers (CSP compliant, no inline handlers)
- CORS configured for localhost in development

### Frontend Dependencies
```bash
# Charts and fonts are installed locally
npm install recharts @fontsource/jetbrains-mono @fontsource/press-start-2p
```

---

## 📚 Additional Resources

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Google Gemini**: https://ai.google.dev/
- **Ollama**: https://ollama.ai/
- **PostgreSQL**: https://www.postgresql.org/docs/

---

## 🎉 You're All Set!

NexusLog is now ready to capture and organize all your ideas! 🧠

**Quick Start Commands:**

```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate  # Windows
python app.py

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Telegram Bot
cd backend
python telegram_bot.py
```

Enjoy your AI-powered idea management system! 🚀
