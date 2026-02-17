# Handover 2 - 17 Feb 2026

## 🚀 Accomplished (The Big Wins)

1.  **Vercel Deployment Fixed (Webhook Handler)**
    *   **Result:** The bot now successfully receives and processes messages on Vercel without crashing.
    *   **Fix:** Replaced the heavy `Application` class with a **stateless `WebhookHandler`** (`backend/webhook_handler.py`) that uses raw HTTP calls. This solved the "Event Loop" error.

2.  **YouTube Processing Fixed**
    *   **Result:** YouTube links no longer crash on Vercel IPs.
    *   **Fix:** Updated `content_extractor.py` to use `extract_flat=True` (metadata only) and added an **oEmbed fallback** + independent transcript fetching.

3.  **Prompt Analysis**
    *   **Finding:** We confirmed that `webhook_handler.py` uses its own **Unified AI Prompt** (Prompt 2) which overrides the default one. This means there is only **1 AI call per message**.

---

## 🚧 Current Status & Next Steps

### 1. Simplify AI Processing (High Priority)
The current flow is too complex and heavy.
*   **Action:** Remove OCR and heavy image analysis code (we just need the file ID and basic type).
*   **Action:** Remove video transcription/analysis code (just get metadata).
*   **Goal:** Inputs should be handled as "Message with Context" rather than "Deep Analysis".

### 2. Unify & Dynamic Prompts
*   **Problem:** The current Webhook Prompt uses a **HARDCODED list of categories** ("Content Ideas", "VibeCoding Projects", etc.). It ignores new categories added to the DB.
*   **Action:** Update `webhook_handler.py` to fetch categories from the DB and inject them into the prompt dynamically.
*   **Action:** Consolidate the prompt logic into a single source of truth.

### 3. Fix Trading Journal
*   **Problem:** Trading journal entries are not reliably syncing to Google Sheets.
*   **Action:**
    *   Review `_handle_trade_journal` in `webhook_handler.py`.
    *   Ensure the AI prompt reliably extracts `{date, stock_symbol, intent: "trade_journal"}`.
    *   Test with specific inputs like "Sold 10 AAPL at 150".

### 4. Flow Diagram (Mental Model)
*   **Text:** `Webhook` -> `Context` -> `Unified Prompt` -> `DB Entry` (+ Content Idea if applicable).
*   **Link/Media:** `Webhook` -> `ContentExtractor` (Meta only) -> `Context` -> `Unified Prompt` -> `DB Entry`.

## 📂 Key Files
*   `backend/webhook_handler.py`: The **Core Logic** for Vercel. (Stateless).
*   `backend/content_extractor.py`: The **Data Fetcher** (YouTube, Links).
*   `backend/ai_services.py`: The **AI Wrapper** (Gemini/Ollama).
*   `backend/app.py`: The **Entry Point** (Route defs).
