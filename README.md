# 🧠 NexusLog

**Your Neural Nexus for Ideas** - An AI-powered idea logging and management system

![NexusLog Logo](frontend/public/logo.png)

---

## 🌟 Features

- **📱 Telegram Integration**: Send ideas via text, images, voice notes, videos, or links
- **🤖 AI-Powered Processing**: Automatic transcription, OCR, categorization, and content generation
- **📊 Smart Categorization**: AI maintains max 10 categories with intelligent subcategories
- **💡 Content Idea Management**: Track ideas for blogs, YouTube, LinkedIn, shorts, and reels
- **📈 Google Sheets Sync**: Automatically sync content ideas to your spreadsheet
- **🎨 Retro-Geeky UI**: Clean, minimalist interface with a nostalgic vibe
- **📱 PWA Support**: Install as a mobile app
- **🔒 Secure**: Environment-based secrets, no keys in code or git

---

## 🛠️ Tech Stack

### Frontend
- **React** + **Vite** + **Tailwind CSS**
- Retro-themed responsive design
- Progressive Web App (PWA)

### Backend
- **Python** + **Flask**
- **PostgreSQL** database
- **SQLAlchemy** ORM

### AI Services (Configurable)
- **Google Gemini** (Primary - Free tier)
- **Ollama** (Local processing)
- **Replicate** (Fallback)
- **OpenAI** (Optional)

### Integrations
- **Telegram Bot API**
- **Google Sheets API**

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Telegram Bot Token
- Google Gemini API Key

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd nebular-ride
```

2. **Set up environment variables**
```bash
copy .env.template .env
# Edit .env with your credentials
```

3. **Initialize database**
```bash
psql -U postgres -d nexuslog -f database/init_db.sql
```

4. **Install backend dependencies**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

5. **Install frontend dependencies**
```bash
cd frontend
npm install
```

6. **Run the application**

Terminal 1 (Backend):
```bash
cd backend
python app.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Terminal 3 (Telegram Bot):
```bash
cd backend
python telegram_bot.py
```

7. **Access the app**
- Web UI: http://localhost:3000
- API: http://localhost:5000/api

---

## 📖 Full Setup Guide

See [SETUP.md](SETUP.md) for detailed step-by-step instructions.

---

## 🎯 Usage

### Via Telegram

1. Start your bot: `/start`
2. Send any content:
   - **Text**: "content idea for blog: How to use AI"
   - **Image**: Send an image (OCR will extract text)
   - **Voice**: Send a voice note (auto-transcribed)
   - **Video**: Send a video (audio transcribed)

### Via Web UI

1. Go to "Add Entry"
2. Fill in your content
3. Select category or let AI categorize
4. Mark as content idea if applicable
5. Choose output types (blog, YouTube, etc.)

---

## 📁 Project Structure

```
nebular-ride/
├── backend/
│   ├── app.py                 # Flask API
│   ├── models.py              # Database models
│   ├── ai_services.py         # AI provider abstraction
│   ├── telegram_bot.py        # Telegram bot handler
│   ├── category_manager.py    # Smart categorization
│   ├── sheets_integration.py  # Google Sheets sync
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/        # React components
│   │   └── utils/api.js       # API client
│   ├── public/
│   │   ├── manifest.json      # PWA manifest
│   │   └── logo.png
│   └── package.json
├── database/
│   └── init_db.sql            # Database schema
├── .env.template              # Environment template
├── SETUP.md                   # Setup guide
└── README.md                  # This file
```

---

## 🔐 Security

- All secrets stored in `.env` (never committed)
- API keys configured via environment variables
- PostgreSQL with proper user permissions
- CORS configured for production

---

## 🌐 Deployment

### Vercel (Frontend + Serverless Backend)
```bash
cd frontend
vercel
```

### Hostinger (Custom Domain)
- Deploy Flask app to Python hosting
- Upload frontend build to `public_html/nexuslog/`
- Configure environment variables
- Set Telegram webhook

See [SETUP.md](SETUP.md) for detailed deployment instructions.

---

## 🤝 Contributing

This is a personal project, but feel free to fork and customize for your needs!

---

## 📝 License

MIT License - feel free to use and modify!

---

## 🙏 Acknowledgments

- Built with ❤️ using AI pair programming
- Inspired by the need for better idea management
- Retro design inspired by classic developer aesthetics

---

## 📧 Support

For issues or questions, check the [SETUP.md](SETUP.md) troubleshooting section.

---

**Made with 🧠 by NexusLog | Powered by AI**
