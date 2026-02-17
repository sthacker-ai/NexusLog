# Handover Document - 17 Feb 2026

## Overview
This session focused on debugging and deploying the NexusLog application to **Vercel**. The transition from a local VPS strategy to Vercel Serverless Functions introduced significant challenges due to the ephemeral nature of the runtime (Read-Only FS, strict environments, and synchronous/WSGI entry point).

## Major Accomplishments

1.  **Dependency Alignment:**
    *   Resolved conflict between `requests` (versioning) and `vercel-blob`.
    *   Updated `backend/requirements.txt` and verified compatibility.
    *   Ensure root `requirements.txt` acts correctly for Vercel.

2.  **Environment Variable Refactor:**
    *   **Problem:** We had mixed usage of standard env vars (`DATABASE_URL`) and custom ones (`nl_DATABASE_URL`).
    *   **Solution:** Implemented `backend/config.py` with a robust `get_env` helper that **automatically** checks for `nl_` prefixes.
    *   **Scope:** Updated **ALL** backend files (`app.py`, `ai_services.py`, `telegram_bot.py`, `file_storage.py`, `sheets_integration.py`).

3.  **Static Assets & 404s:**
    *   **Problem:** API was 200, but `/logo.svg` was 404, causing errors.
    *   **Solution:** Identified `logo.svg` was missing, `logo.png` existed. Updated `frontend/index.html` and `manifest.json` to use `logo.png`.

4.  **Read-Only Filesystem Patches:**
    *   **Problem:** `OSError: [Errno 30] Read-only file system` crashed the app on startup.
    *   **Fix:** Wrapped file creation (`os.makedirs`) in try-except blocks:
        *   `backend/telegram_bot.py`: Handles log directory creation failure.
        *   `backend/ai_services.py`: Handles debug audio/file saves.
        *   `backend/file_storage.py`: Handles `static/uploads` creation (logs warning on Vercel).
    *   **Result:** App now starts successfully (HTTP 200 on `/api/health` and `/api/analytics`).

5.  **Telegram Webhook Implementation (Partial Success):**
    *   Since Vercel cannot run `polling`, we implemented a **Webhook Route** at `/api/telegram-webhook`.
    *   Refactored `app.py` to handle `POST` updates.
    *   Created `backend/set_telegram_webhook.py` script to configure the webhook easily.

## Current Issue (The Blocker)
**Status:** The application deploys successfully (Green check), and the Web API (frontend) works. However, the **Telegram Bot** fails to process messages.

**Error:**
```
Webhook processing error: This Application was not initialized via `Application.initialize`!
```

**Root Cause:**
*   The `python-telegram-bot` (v20+) library uses an async `Application` class designed for long-running processes.
*   In Vercel (Serverless/WSGI), each request spins up a new environment or reuses one with a **fresh Event Loop**.
*   The `Application` object is bound to the Event Loop it was created in. When a new request arrives with a new loop, the `Application` (even if global) fails because its underlying `httpx` client is closed or mismatched.

**Attempted Fixes:**
1.  **Global Bot Reuse:** Using a single global `tele_bot` in `app.py`. Failed due to closed loop.
2.  **Explicit Initialization:** Added `_is_initialized` flag and manual `await application.initialize()`. Failed with same error.
3.  **Per-Request Instantiation:** Refactored `app.py` to `bot = TelegramBot()` inside the request handler. This forces creation on the *current* loop. **This is the current state, but the user reports the error persists.**

## Recommended Next Steps for New Chat
The `python-telegram-bot` `Application` class is too heavy/stateful for Vercel functions. We should switch to a **stateless / lightweight** approach.

1.  **Switch to `Bot` Class Directly:**
    Instead of using `Application` + Handlers, use the raw `Bot` class to send messages and manually parse the `Update` JSON.
    ```python
    # In app.py
    from telegram import Bot, Update
    bot = Bot(token=...)
    
    @app.route(...)
    async def webhook():
        update = Update.de_json(request.get_json(), bot)
        # Manually route based on update.message.text
        if update.message.text == '/start':
             full_logic...
    ```
    This removes the `Application` lifecycle complexity entirely.

2.  **Use a Synchronous Library:**
    Consider `pyTelegramBotAPI` (`telebot`) for Vercel. It is synchronous by default and works perfectly with Flask/WSGI without `asyncio` friction.
    *   Currently, we are forcing async code into sync Flask, which is fragile.

3.  **Alternative: Verify `Per-Request` Fix:**
    Ensure the `app.py` code *actually* deployed with the `bot = TelegramBot()` change. If it did, and still fails, then option 1 or 2 is mandatory.

## File Locations
*   `backend/app.py`: Main entry point, webhook route.
*   `backend/telegram_bot.py`: Bot logic (currently using `Application`).
*   `backend/config.py`: Environment variable helper.
*   `backend/set_telegram_webhook.py`: Script to set webhook URL.
