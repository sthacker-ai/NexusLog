# NexusLog - Implementation Plan

**AI-Powered Idea Logger with Telegram Integration**

NexusLog is a modular, intelligent note-taking system that captures ideas from multiple sources (Telegram messages, images, videos, audio, links), processes them with AI, categorizes them intelligently, and presents them in a clean, retro-geeky UI.

This was created when i moved this from office PC to personal PC, so this was created so it can be used as handoff.
---

## User Review Required

> [!IMPORTANT]
> **AI Service Strategy**: The app will prioritize free/local AI options:
> - **Primary**: Google Gemini Flash 2.0/1.5 (free tier, you already have API key)
> - **Local**: Ollama for basic text processing (already installed)
> - **Fallback**: Replicate for specialized tasks (costs money, configurable via UI)
> - All AI providers are fully configurable via UI

> [!IMPORTANT]
> **PostgreSQL Setup**: You'll need to create a PostgreSQL database named `nexuslog`. I'll provide SQL scripts and step-by-step instructions.

> [!IMPORTANT]
> **Telegram Bot**: You'll need to create a Telegram bot via BotFather and obtain a bot token. Instructions will be provided.

> [!WARNING]
> **Security**: Secrets will be stored in environment variables (Vercel for production OR Hostinger custom deployment, `.env` for local). The `.env` file will NOT be committed to git. A `.env.template` will be provided. Deployment instructions will cover both Vercel and Hostinger (thinkbits.in/nexuslog) options.

---

## Proposed Changes

### Core Architecture

```mermaid
graph TB
    TG[Telegram Bot] --> API[Flask Backend API]
    UI[React Frontend] --> API
    API --> DB[(PostgreSQL)]
    API --> AI[AI Services Layer]
    AI --> OCR[OCR Service]
    AI --> STT[Speech-to-Text]
    AI --> TTS[Text-to-Speech]
    AI --> LLM[LLM for Categorization]
    API --> GS[Google Sheets API]
    API --> FS[File Storage]
```

---

### Backend Components

#### [NEW] [app.py](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/backend/app.py)
Main Flask application with API routes:
- `/api/entries` - CRUD operations for ideas/notes
- `/api/categories` - Category management
- `/api/telegram/webhook` - Telegram webhook endpoint
- `/api/process` - Manual processing trigger
- `/api/config` - Configuration management (AI services, TTS settings, etc.)
- `/api/sheets/sync` - Google Sheets synchronization

#### [NEW] [models.py](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/backend/models.py)
SQLAlchemy models:
- `Entry` - Raw and processed content storage
- `Category` - Dynamic category system with subcategories
- `Project` - Project tracking for vibe coding ideas
- `ContentIdea` - Content creation ideas with output types
- `Config` - App configuration storage

#### [NEW] [ai_services.py](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/backend/ai_services.py)
Modular AI service layer with provider abstraction (prioritizes free/local):
- `AIServiceProvider` - Base class for AI providers
- `GeminiProvider` - Primary provider (Gemini Flash 2.0/1.5, free tier)
- `OllamaProvider` - Local processing for basic text tasks
- `ReplicateProvider` - Fallback for specialized tasks (costs money)
- `OpenAIProvider` - Optional (if user has API key)
- Methods: `transcribe_audio()`, `transcribe_video()`, `ocr_image()`, `text_to_speech()`, `categorize_content()`
- Smart fallback chain: Ollama → Gemini → Replicate (configurable)

#### [NEW] [telegram_bot.py](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/backend/telegram_bot.py)
Telegram bot handler:
- Message type detection (text, image, video, audio, link)
- Media download and storage
- Input parsing for category hints and content type flags
- Response generation (text + optional voice)
- Integration with AI processing pipeline

#### [NEW] [category_manager.py](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/backend/category_manager.py)
Smart category management:
- Maintains max 10 top-level categories
- AI-powered category suggestion
- Checks existing categories before creating new ones
- Subcategory support (e.g., VibeCoding → Project1, Project2)

#### [NEW] [sheets_integration.py](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/backend/sheets_integration.py)
Google Sheets API integration:
- Append content ideas to specified sheet
- Format: Idea description + AI-generated prompt

---

### Database Schema

#### [NEW] [init_db.sql](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/database/init_db.sql)
PostgreSQL schema initialization:

```sql
-- Categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entries table (raw + processed)
CREATE TABLE entries (
    id SERIAL PRIMARY KEY,
    raw_content TEXT,
    processed_content TEXT,
    content_type VARCHAR(50), -- text, image, video, audio, link
    file_path VARCHAR(500),
    category_id INTEGER REFERENCES categories(id),
    subcategory_id INTEGER REFERENCES categories(id),
    source VARCHAR(50) DEFAULT 'telegram',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content ideas table
CREATE TABLE content_ideas (
    id SERIAL PRIMARY KEY,
    entry_id INTEGER REFERENCES entries(id),
    idea_description TEXT,
    ai_prompt TEXT,
    output_types JSONB, -- ["blog", "youtube", "linkedin", "shorts"]
    status VARCHAR(50) DEFAULT 'idea',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    description TEXT,
    category_id INTEGER REFERENCES categories(id),
    tasks JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Config table
CREATE TABLE config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Frontend Components

#### [NEW] [App.jsx](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/src/App.jsx)
Main React application with routing:
- Dashboard
- Categories view
- Manual input form
- Settings/Config
- Idea list view

#### [NEW] [index.css](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/src/index.css)
Retro-geeky theme with:
- Pixel/monospace fonts (Press Start 2P, JetBrains Mono)
- Light theme with pastel accents
- Rounded corners, subtle shadows
- Hover animations
- CSS variables for theming

#### [NEW] [Dashboard.jsx](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/src/components/Dashboard.jsx)
Main dashboard showing:
- Recent entries
- Category breakdown
- Quick stats
- Quick add button

#### [NEW] [CategoryManager.jsx](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/src/components/CategoryManager.jsx)
Category management interface:
- Create/edit/delete categories
- Subcategory management
- Visual hierarchy display

#### [NEW] [ManualInput.jsx](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/src/components/ManualInput.jsx)
Manual entry form with:
- Text input
- Category/subcategory dropdowns
- Content type checkboxes (blog, youtube, linkedin, shorts)
- "AI validate" checkbox
- File upload support

#### [NEW] [IdeaList.jsx](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/src/components/IdeaList.jsx)
Filterable idea list:
- Filter by category, subcategory, content type
- Search functionality
- Card-based layout with rounded corners
- Hover effects

#### [NEW] [Settings.jsx](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/src/components/Settings.jsx)
Configuration UI:
- AI provider selection (Replicate, OpenAI, Gemini, etc.)
- API key management
- TTS voice selection
- Google Sheets configuration
- Telegram bot status

#### [NEW] [manifest.json](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/public/manifest.json)
PWA manifest for mobile installation

---

### Configuration & Setup Files

#### [NEW] [.env.template](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/.env.template)
Template for environment variables:
```
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/nexuslog

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# AI Services (Priority: Gemini → Ollama → Replicate)
GOOGLE_AI_API_KEY=your_gemini_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
REPLICATE_API_KEY=optional_fallback_key
OPENAI_API_KEY=optional_if_you_have_it

# Google Sheets (you already have credentials)
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials/google-sheets-creds.json
GOOGLE_SHEET_ID=your_sheet_id_here

# Flask
FLASK_SECRET_KEY=generate_random_secret_key

# Deployment (Vercel OR Hostinger)
DEPLOYMENT_TARGET=hostinger  # or 'vercel'
CUSTOM_DOMAIN=thinkbits.in/nexuslog
```

#### [NEW] [SETUP.md](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/SETUP.md)
Comprehensive setup instructions:
1. PostgreSQL database creation
2. Telegram bot creation via BotFather
3. Gemini API key setup (you already have this)
4. Ollama local setup verification
5. Google Sheets credentials configuration (you already have this)
6. Local development setup
7. Deployment options:
   - Option A: Vercel deployment
   - Option B: Hostinger deployment (thinkbits.in/nexuslog)

#### [NEW] [requirements.txt](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/backend/requirements.txt)
Python dependencies:
- Flask, Flask-CORS
- SQLAlchemy, psycopg2
- python-telegram-bot
- requests (for AI APIs)
- google-auth, google-api-python-client
- python-dotenv

#### [NEW] [package.json](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/package.json)
Frontend dependencies:
- React, React Router
- Tailwind CSS
- Axios
- Vite

---

### Branding

#### [NEW] [logo.svg](file:///c:/Users/STHACKER/.gemini/antigravity/playground/nebular-ride/frontend/public/logo.svg)
NexusLog logo - retro pixel-style brain/network icon

---

## Verification Plan

### Automated Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend build test
cd frontend
npm run build
```

### Manual Verification

1. **Database Setup**: Run SQL scripts and verify tables created
2. **Telegram Bot**: 
   - Send text message → verify stored in DB
   - Send image → verify OCR processing
   - Send audio → verify transcription
   - Send video link → verify processing
   - Verify voice response (British male voice)
3. **UI Testing**:
   - Create category manually
   - Add entry via manual form
   - Verify AI validation checkbox works
   - Test category/subcategory dropdowns
   - Test content type checkboxes
   - Verify mobile responsiveness
4. **AI Processing**:
   - Verify smart categorization (doesn't create duplicate categories)
   - Verify content idea prompt generation
   - Test with different AI providers via settings
5. **Google Sheets**: Verify content ideas appear in sheet
6. **PWA**: Test "Add to Home Screen" on mobile

---

## Project Structure

```
nebular-ride/
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── ai_services.py
│   ├── telegram_bot.py
│   ├── category_manager.py
│   ├── sheets_integration.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── components/
│   │       ├── Dashboard.jsx
│   │       ├── CategoryManager.jsx
│   │       ├── ManualInput.jsx
│   │       ├── IdeaList.jsx
│   │       └── Settings.jsx
│   ├── public/
│   │   ├── manifest.json
│   │   └── logo.svg
│   ├── package.json
│   └── vite.config.js
├── database/
│   └── init_db.sql
├── .env.template
├── SETUP.md
└── README.md
```
