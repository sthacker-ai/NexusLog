# NexusLog - Product Requirements Document

## Overview
**NexusLog** is an AI-powered idea management system that captures thoughts through Telegram (voice, text, images, links) and organizes them intelligently using AI.

**Tagline:** Your Neural Nexus for Ideas

---

## Current Features (Implemented)

### Core Features
- **Telegram Integration**: Bot receives text, voice notes, images, videos, links
- **AI Processing**: Gemini-powered transcription, categorization, title generation
- **Smart Categories**: AI suggests categories (max 10), auto-create if needed
- **Content Ideas**: Flag entries as blog/YouTube/LinkedIn/Shorts/Reels content

### UI Features
- **Dashboard**: Stats, activity charts, usage insights, recent entries
- **Timeline**: Vertical timeline view of daily activity
- **Entry List**: Filter by type, expandable details
- **Ideas Page**: Content ideas with markdown rendering
- **Category Manager**: CRUD for categories with hierarchy
- **System Status**: Service health, bot/backend logs, AI usage analytics

### Enhancements
- **AI Usage Tracking**: Recharts-based dual-axis chart (tokens + requests)
- **TTS Integration**: Qwen3-TTS via Replicate for audio generation  
- **IST Timestamps**: All times displayed in Indian Standard Time
- **Log Pagination**: 50 lines default, "Load More" for history
- **Token Redaction**: Sensitive tokens hidden from displayed logs
- **Local Fonts**: No CDN dependencies per security guidelines
- **YouTube Video Embeds**: Native iframe embeds (replaced ReactPlayer), 480px max-width, works in both collapsed and expanded views
- **X/Twitter Link Handling**: Graceful fallback for X.com links (filters JS-unavailable messages)
- **Async Telegram Handlers**: All blocking I/O wrapped in `asyncio.run_in_executor()` to prevent timeouts
- **Markdown Typography**: `@tailwindcss/typography` plugin for proper prose styling (lists, headings, spacing)
- **Link Behavior**: All links open in new tabs, raw URLs hidden from collapsed view, "Open Link" label
- **Bold Entry Titles**: Titles displayed as bold `<h3>` above metadata badges
- **"To Learn" Category**: New category with subcategories "Reading List" and "Videos"
- **Markdown Links**: `remark-gfm` for auto-linking URLs + custom `MarkdownLink` component

---

## Roadmap

### ✅ Completed
- **Display**: Embed images/videos/GIFs for direct playback/viewing with lightbox
- **Image/GIF Display**: Backend path fixes, animation handler, frontend lightbox + thumbnails
- **YouTube Video Embeds**: Native iframe embeds, works in collapsed and expanded views
- **X/Twitter Link Handling**: Graceful fallback for X.com links
- **Async Telegram Handlers**: All blocking I/O wrapped in `asyncio.run_in_executor()`
- **Markdown Typography**: `@tailwindcss/typography` + `remark-gfm` for proper prose styling
- **Link Behavior**: All links open in new tabs, raw URLs hidden from collapsed view
- **Bold Entry Titles**: Titles displayed as bold `<h3>` above metadata badges
- **"To Learn" Category**: New category with subcategories
- **Security Audit**: Local fonts, token redaction, CSP compliance

### 🔮 Future Release
- [ ] **Simplified AI Processing**: Text/Voice — grammar/spelling fix only (no summarization). Media — save as-is with basic metadata
- [ ] **Google Sheets Integration (Trading Journal)**: Trigger on "Trading Journal" keyword, match Date + Stock Symbol, update specific columns
- [ ] **Multi-Input AI Parsing**: Single voice note → multiple entries (refined logic)
- [ ] **Model Stacking**: Priority-based multi-model support
- [ ] **Notes Section**: OneNote-like hierarchical notes (3 layers)
- [ ] **Deployment**: Host on cloud platform (see hosting analysis below)
- [ ] **Image + Voice Combo**: Smart multimodal input processing
- [ ] **Chart Legend Fix**: Free limit label in Recharts
- [ ] **Article Image Extraction**: OCR images embedded within web articles/blogs


---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Backend | Python, Flask, SQLAlchemy |
| Database | PostgreSQL |
| AI | Google Gemini (primary), Replicate (TTS/fallback), Ollama (local) |
| Integrations | Telegram Bot API, Google Sheets API |

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/system-status` | GET | Service status |
| `/api/usage` | GET | AI usage stats |
| `/api/logs/{service}` | GET | Service logs (paginated) |
| `/api/entries` | GET/POST | Entry CRUD |
| `/api/categories` | GET/POST | Category CRUD |
| `/api/ideas` | GET/POST | Content ideas |
| `/api/timeline` | GET | Timeline data |

---

## Security

- All secrets in `.env` (never committed)
- Token redaction in log display
- Local fonts only (no CDN)
- CORS configured per environment
- React event handlers (CSP compliant)

---

*Last updated: 2026-02-16*
