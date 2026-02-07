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

---

## Roadmap (Planned)

### Near-Term
- [ ] **Multi-Input AI Parsing**: Single voice note → multiple entries
- [ ] **Google Sheets Cell Update**: Voice note updates specific cell by identifiers
- [ ] **Multiple AI APIs**: Groq + Ollama fallback system

### Medium-Term
- [ ] **Notes Section**: OneNote-like hierarchical notes (3 layers)
- [ ] **Hostinger Deployment**: thinkbits.in/nexuslog
- [ ] **Image + Voice Combo**: Smart multimodal input processing

### Deferred
- [ ] **Chart Legend Fix**: Free limit label in Recharts

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

*Last updated: 2026-02-07*
