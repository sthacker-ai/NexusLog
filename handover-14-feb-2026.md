# NexusLog — Handover Document (Feb 14, 2026)

## Project Overview
**NexusLog** is a personal knowledge management system. Users send content (text, links, images, audio, video) to a **Telegram bot**, which processes it via AI (Gemini) and stores it in **PostgreSQL**. A **React frontend** displays all entries with filtering, search, and media rendering.

**Stack**: Python/Flask backend, React/Vite frontend, PostgreSQL, Telegram Bot API, Google Gemini AI.

**Location**: `c:\My stuff\My Vibe Coding Projects\NexusLog`

---

## What Was Completed This Session

### 1. YouTube Video Player Fix ✅ VERIFIED
**Problem**: YouTube videos stored correctly in DB but never showed a player on frontend.

**Root cause found**: `ReactPlayer` library was **silently failing** — rendered DOM but showed nothing (likely due to `light={true}` thumbnail loading or internal player detection).

**Fix applied**:
- Replaced `ReactPlayer` with **native `<iframe>` YouTube embed** (cannot silently fail)
- Added `getYouTubeVideoId()` helper that extracts 11-char video ID from any YouTube URL format
- Added `getVideoUrl()` helper that checks `entry_metadata.source_url` first, then falls back to content regex
- Video embed now shows in **both collapsed AND expanded** entry views
- Backend now stores `source_url` in `entry_metadata` JSON field
- Ran `backfill_source_url.py` to populate existing 8 YouTube entries

**Files changed**:
- `backend/telegram_bot.py` — `_process_and_store()` accepts `source_url`, `handle_text()` extracts and passes it
- `frontend/src/components/EntryList.jsx` — Removed ReactPlayer, added iframe embed logic

> [!NOTE]
> **Verified on Feb 16, 2026.** YouTube iframe embeds confirmed working. Video frames constrained to 480px max-width. Bold titles display above metadata badges.

### 2. X/Twitter Extraction Fix
- `content_extractor.py` `extract_url_content()` now filters "JavaScript is not available" messages
- Falls back to `title = "X Post"` and `content = "View original post on X: {url}"` for X.com/Twitter.com links
- Fixed `UnboundLocalError` where `title` was accessed before metadata extraction

### 3. Async Handler Optimization
- All blocking I/O in `telegram_bot.py` handlers (`handle_text`, `handle_image`, `handle_audio`, `handle_video`) wrapped in `asyncio.run_in_executor()` to prevent Telegram `TimedOut` errors

### 4. Markdown Link Rendering
- Installed `remark-gfm` for proper link auto-detection in `ReactMarkdown`
- Removed manual `linkify()` regex hack

---

## 3 Open Issues — ALL RESOLVED ✅

### Issue 1: Verify YouTube iframe ✅ RESOLVED
Verified on Feb 16, 2026. YouTube iframe embeds render correctly. Video frames constrained to 480px. Bold titles display above metadata.

### Issue 2: X/Twitter article processing ✅ RESOLVED
User confirmed X/Twitter links process correctly through the Telegram bot and display on the frontend without errors.

### Issue 3: Links not clickable on frontend ✅ RESOLVED
- Installed `@tailwindcss/typography` and registered in `tailwind.config.js` — `prose` classes now work
- Added custom `MarkdownLink` component — all links open in new tabs (`target="_blank"`)
- Raw URLs hidden from collapsed entry view via `stripUrls()` helper
- "Open Link" label replaces old "Open video link" text

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/telegram_bot.py` | All Telegram handlers, AI processing, DB storage |
| `backend/content_extractor.py` | URL detection, YouTube extraction, web scraping |
| `backend/ai_services.py` | Gemini AI interface (vision, text, token tracking) |
| `backend/models.py` | SQLAlchemy models (Entry, Category, ContentIdea, etc.) |
| `backend/app.py` | Flask REST API |
| `frontend/src/components/EntryList.jsx` | Main entry rendering (video embeds, markdown, media) |
| `frontend/src/utils/api.js` | API client |
| `backend/backfill_source_url.py` | One-time script (already ran) to add source_url to old entries |
| `backend/debug_youtube.py` | Diagnostic script to query DB for YouTube entries |

## Environment
- Backend virtual env: `backend/venv/`
- Start everything: `start_app.bat` (runs backend on port 5000, frontend on port 3000)
- Database: PostgreSQL (connection string in `.env` as `DATABASE_URL`)
- `.env` contains: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `GOOGLE_API_KEY`, `GOOGLE_SHEET_ID`
