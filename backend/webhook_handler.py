"""
Stateless Telegram Webhook Handler for Vercel Serverless

Uses the raw telegram.Bot class instead of Application to avoid
event loop lifecycle issues in serverless environments.

This module handles incoming webhook updates synchronously,
using httpx to send Telegram API calls and reusing the existing
AI/DB/Sheets processing logic.
"""
import os
import re
import time
import json
import logging
import tempfile
from io import BytesIO
from typing import Dict, List, Optional, Any

import httpx

from models import Entry, ContentIdea, Category, get_session
from ai_services import AIServiceManager
from category_manager import CategoryManager
from sheets_integration import SheetsIntegration
from content_extractor import get_content_extractor
from file_storage import storage
from config import get_env

logger = logging.getLogger(__name__)

# Telegram Bot API base URL
TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class WebhookHandler:
    """
    Stateless webhook handler for processing Telegram updates in serverless.
    
    Unlike TelegramBot (which uses Application + async handlers),
    this class uses raw HTTP calls to the Telegram Bot API and
    processes everything synchronously.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.api_base = f"https://api.telegram.org/bot{token}"
        self.file_api_base = f"https://api.telegram.org/file/bot{token}"
        
        # Reuse the same service managers as TelegramBot
        self.ai_manager = AIServiceManager()
        self.category_manager = CategoryManager()
        self.content_extractor = get_content_extractor()
        
        try:
            self.sheets = SheetsIntegration()
        except Exception as e:
            logger.warning(f"Google Sheets not configured: {e}")
            self.sheets = None
    
    # ========================================
    # Telegram API helpers (sync via httpx)
    # ========================================
    
    def _api_call(self, method: str, **kwargs) -> dict:
        """Make a synchronous Telegram Bot API call."""
        url = f"{self.api_base}/{method}"
        try:
            response = httpx.post(url, json=kwargs, timeout=30)
            result = response.json()
            if not result.get('ok'):
                logger.error(f"Telegram API error: {result}")
            return result
        except Exception as e:
            logger.error(f"Telegram API call failed ({method}): {e}")
            return {'ok': False, 'error': str(e)}
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = None) -> dict:
        """Send a text message to a chat."""
        # Telegram has a 4096 character limit
        if len(text) > 4000:
            text = text[:4000] + "..."
        params = {'chat_id': chat_id, 'text': text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        return self._api_call('sendMessage', **params)
    
    def get_file(self, file_id: str) -> Optional[dict]:
        """Get file info from Telegram."""
        result = self._api_call('getFile', file_id=file_id)
        if result.get('ok'):
            return result['result']
        return None
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """Download a file from Telegram servers."""
        url = f"{self.file_api_base}/{file_path}"
        try:
            response = httpx.get(url, timeout=60)
            if response.status_code == 200:
                return response.content
            logger.error(f"File download failed: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"File download error: {e}")
            return None
    
    # ========================================
    # Update routing
    # ========================================
    
    def process_update(self, update_json: dict):
        """
        Main entry point: route an incoming update to the appropriate handler.
        Fully synchronous — no asyncio needed.
        """
        try:
            message = update_json.get('message')
            if not message:
                logger.info("Update has no message, skipping (could be edited_message, callback, etc.)")
                return
            
            chat_id = message['chat']['id']
            
            # Route based on content type
            if message.get('text'):
                text = message['text']
                # Check for commands
                if text.startswith('/start'):
                    self._handle_start(chat_id)
                elif text.startswith('/help'):
                    self._handle_help(chat_id)
                elif text.startswith('/categories'):
                    self._handle_categories(chat_id)
                else:
                    self._handle_text(chat_id, message)
            elif message.get('photo'):
                self._handle_photo(chat_id, message)
            elif message.get('voice') or message.get('audio'):
                self._handle_audio(chat_id, message)
            elif message.get('video'):
                self._handle_video(chat_id, message)
            elif message.get('animation'):
                self._handle_animation(chat_id, message)
            elif 'document' in message:
                self._handle_document(message['document'], chat_id, message.get('caption'))
            else:
                self.send_message(chat_id, "🤔 I don't know how to handle this type of content yet.")
                
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}", exc_info=True)
            # Try to inform the user
            try:
                chat_id = update_json.get('message', {}).get('chat', {}).get('id')
                if chat_id:
                    self.send_message(chat_id, f"❌ Error processing your message: {str(e)[:200]}")
            except Exception:
                pass
    
    # ========================================
    # Command handlers
    # ========================================
    
    def _handle_start(self, chat_id: int):
        self.send_message(chat_id, (
            "🧠 Welcome to NexusLog!\n\n"
            "I'm your AI-powered idea logger. Send me:\n"
            "- 📝 Text messages\n"
            "- 🖼️ Images\n"
            "- 🎤 Voice notes\n"
            "- 🎥 Videos\n"
            "- 🔗 Links\n\n"
            "I'll process, categorize, and store everything for you!\n\n"
            "Use /help to see all commands."
        ))
    
    def _handle_help(self, chat_id: int):
        self.send_message(chat_id, (
            "📚 NexusLog Commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/categories - List categories\n\n"
            "💡 How to use:\n"
            "- Just send me any content!\n"
            "- Add \"content idea\" to mark as content\n"
            "- Specify output types: \"blog\", \"youtube\", \"linkedin\", \"shorts\", \"reels\"\n"
            "- Example: \"content idea for blog and youtube: How to build AI apps\"\n\n"
            "I'll automatically categorize and process everything! 🚀"
        ))
    
    def _handle_categories(self, chat_id: int):
        categories = self.category_manager.get_all_categories()
        if not categories:
            self.send_message(chat_id, "No categories found.")
            return
        
        text = "📂 Categories\n\n"
        for cat in categories:
            text += f"• {cat['name']}\n"
            if cat.get('subcategories'):
                for sub in cat['subcategories']:
                    text += f"  - {sub['name']}\n"
        
        self.send_message(chat_id, text)
    
    # ========================================
    # Content handlers
    # ========================================
    
    def _handle_text(self, chat_id: int, message: dict):
        """Handle text messages with full AI processing."""
        text = message['text']
        reply_to = message.get('reply_to_message')
        
        self.send_message(chat_id, "🧠 Processing with AI...")
        
        try:
            # Extract all content (URLs, YouTube, web pages)
            extracted = self.content_extractor.extract_all_content(
                text=text,
                reply_to_message=reply_to
            )
            
            # Show extraction notes if any
            if extracted.get('extraction_notes'):
                notes = "\n".join(f"• {n}" for n in extracted['extraction_notes'][:3])
                self.send_message(chat_id, f"📥 Extracted:\n{notes}")
            
            # Process with unified AI
            ai_items = self._unified_ai_process(extracted)
            
            # Parse metadata for output types
            metadata = self._parse_input_metadata(text)
            
            # Determine content type and extract source URL
            has_youtube = len(extracted.get('youtube_content', [])) > 0
            has_urls = len(extracted.get('url_content', [])) > 0
            
            # Fix YouTube Type: If it's YouTube, ALWAYS be 'video' to match frontend filter
            if has_youtube:
                content_type = 'video'
            elif has_urls:
                content_type = 'link'
            else:
                content_type = 'text'
            
            # Extract the original source URL
            source_url = None
            if has_youtube:
                source_url = extracted['youtube_content'][0].get('url', '')
            elif has_urls:
                source_url = extracted['url_content'][0].get('url', '')
            elif extracted.get('urls', {}).get('youtube'):
                source_url = extracted['urls']['youtube'][0]
            elif extracted.get('urls', {}).get('generic'):
                source_url = extracted['urls']['generic'][0]
            
            entry_ids = []
            
            # Process each AI item
            for ai_result in ai_items:
                entry_id = self._process_and_store(
                    content=ai_result['processed_content'],
                    content_type=content_type if len(entry_ids) == 0 else 'text',
                    is_content_idea=metadata['is_content_idea'] or ai_result['is_content_idea'],
                    output_types=metadata['output_types'],
                    category_hint=ai_result['category'],
                    subcategory_hint=ai_result.get('subcategory'),
                    title=ai_result['title'],
                    source_url=source_url
                )
                entry_ids.append((entry_id, ai_result))
            
            # Build confirmation message
            confirmation = self._build_text_confirmation(entry_ids, content_type)
            
            # Handle Trading Journal for first item
            if entry_ids:
                _, first_ai = entry_ids[0]
                if first_ai.get('intent') == 'trade_journal':
                    trade_msg = self._handle_trade_journal(first_ai)
                    confirmation += trade_msg
            
            self.send_message(chat_id, confirmation)
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}", exc_info=True)
            # Fallback: save as-is
            metadata = self._parse_input_metadata(text)
            entry_id = self._process_and_store(
                content=text,
                content_type='text',
                is_content_idea=metadata['is_content_idea'],
                output_types=metadata['output_types']
            )
            self.send_message(chat_id, f"✅ Saved (basic mode). Entry ID: {entry_id}")
    
    def _handle_photo(self, chat_id: int, message: dict):
        """Handle image messages."""
        self.send_message(chat_id, "🖼️ Processing image...")
        
        try:
            # Get the highest resolution photo
            photo_data = message['photo'][-1]
            file_id = photo_data['file_id']
            file_name = photo_data.get('file_unique_id', file_id) + '.jpg' # Use unique_id for filename
            
            file_info = self.get_file(file_id)
            if not file_info:
                self.send_message(chat_id, "❌ Failed to get image from Telegram")
                return
            
            file_data = self.download_file(file_info['file_path'])
            if not file_data:
                self.send_message(chat_id, "❌ Failed to download image")
                return
            
            # Save to persistent storage (Local or Blob)
            filename = f"images/{file_id}_{file_name}"
            persistent_path = storage.save_file(file_data, filename, content_type='image/jpeg')
            
            if not persistent_path:
                persistent_path = "storage_failed" # Placeholder to avoid DB error
            
            caption = message.get('caption', '')
            
            # Build extracted content for unified AI
            extracted = {'text': caption}
            
            # Analyze image with AI if available
            try:
                # DISABLED for Vercel performance/cost - relying on user caption
                # image_analysis = self.ai_manager.analyze_image(file_data)
                # extracted['image_analysis'] = image_analysis
                extracted['image_analysis'] = caption or "Image uploaded"
            except Exception as e:
                logger.warning(f"Image analysis failed: {e}")
                extracted['image_analysis'] = caption or "Image uploaded"
            
            # Process with unified AI
            ai_items = self._unified_ai_process(extracted)
            
            metadata = self._parse_input_metadata(caption) if caption else {
                'is_content_idea': False, 'output_types': [], 'clean_text': ''
            }
            
            entry_ids = []
            for ai_result in ai_items:
                entry_id = self._process_and_store(
                    content=ai_result['processed_content'],
                    content_type='image' if len(entry_ids) == 0 else 'text',
                    file_path=persistent_path if len(entry_ids) == 0 else None,
                    is_content_idea=metadata.get('is_content_idea', False) or ai_result['is_content_idea'],
                    output_types=metadata.get('output_types', []),
                    category_hint=ai_result['category'],
                    subcategory_hint=ai_result.get('subcategory'),
                    title=ai_result['title']
                )
                entry_ids.append((entry_id, ai_result))
            
            # Build confirmation
            if len(entry_ids) == 1:
                entry_id, ai_result = entry_ids[0]
                confirmation = f"✅ Image analyzed! Entry ID: {entry_id}\n"
                confirmation += f"📁 Category: {ai_result['category']}\n"
                preview = ai_result['processed_content'][:400]
                if len(ai_result['processed_content']) > 400:
                    preview += "..."
                confirmation += f"\n📋 Analysis:\n{preview}"
            else:
                confirmation = f"✅ Created {len(entry_ids)} entries from image!\n\n"
                for i, (entry_id, ai_result) in enumerate(entry_ids, 1):
                    confirmation += f"{i}. {ai_result['title'][:40]} (ID: {entry_id})\n"
            
            self.send_message(chat_id, confirmation)
            
        except Exception as e:
            logger.error(f"Photo processing failed: {e}", exc_info=True)
            self.send_message(chat_id, f"❌ Error processing image: {str(e)[:200]}")
    
    def _handle_audio(self, chat_id: int, message: dict):
        """Handle voice notes and audio files."""
        self.send_message(chat_id, "🎙️ Transcribing voice note...")
        
        try:
            audio = message.get('voice') or message.get('audio')
            file_id = audio['file_id']
            file_unique_id = audio.get('file_unique_id')
            
            # --- DEDUPLICATION CHECK ---
            if file_unique_id:
                session = get_session()
                try:
                    # Fix: use cast for JSONB/JSON text comparison
                    from sqlalchemy import cast, String
                    existing = session.query(Entry).filter(
                        cast(Entry.entry_metadata['file_unique_id'], String) == f'"{file_unique_id}"'
                    ).first()
                    
                    if not existing:
                        # Fallback: sometimes it's stored without quotes in JSONB
                        existing = session.query(Entry).filter(
                             cast(Entry.entry_metadata['file_unique_id'], String) == file_unique_id
                        ).first()

                    if existing:
                        logger.info(f"Skipping duplicate audio processing for unique_id: {file_unique_id}")
                        if existing.raw_content == "PROCESSING_LOCK":
                             self.send_message(chat_id, "⏳ Still processing this audio...")
                        else:
                             self.send_message(chat_id, f"⚠️ I already processed this audio (Entry ID: {existing.id}).")
                        return
                    
                    # CREATE LOCK ENTRY
                    lock_entry = Entry(
                        raw_content="PROCESSING_LOCK",
                        processed_content="Processing...",
                        content_type='audio',
                        file_path="pending",
                        source='telegram',
                        entry_metadata={'file_unique_id': file_unique_id}
                    )
                    session.add(lock_entry)
                    session.commit()
                    lock_entry_id = lock_entry.id
                    
                except Exception as e:
                    logger.error(f"Deduplication/Lock check failed: {e}")
                    # If lock fails, we might still want to proceed, or abort? 
                    # Abort safest to prevent dupes
                    return
                finally:
                    session.close()
            else:
                lock_entry_id = None
            # ---------------------------

            file_name = f"{file_unique_id}.ogg" if file_unique_id else f"{file_id}.ogg"
            
            file_info = self.get_file(file_id)
            if not file_info:
                self.send_message(chat_id, "❌ Failed to get audio from Telegram")
                return
            
            file_data = self.download_file(file_info['file_path'])
            if not file_data:
                self.send_message(chat_id, "❌ Failed to download audio")
                return
            
            # 1. Save to temp for transcription
            temp_path = storage.save_temp(file_data, suffix='.ogg')
            
            # 2. Transcribe (requires local file)
            transcription = ""
            if temp_path:
                try:
                    transcription = self.ai_manager.transcribe_audio(temp_path)
                finally:
                    # Cleanup temp
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete temp audio file {temp_path}: {e}")
            
            # 3. Save to persistent storage
            filename = f"audio/{file_id}_{file_name}"
            persistent_path = storage.save_file(file_data, filename, content_type='audio/ogg')
            
            if not persistent_path:
                persistent_path = "storage_failed"
                
            self.send_message(chat_id, "🧠 Processing with AI...")
            
            reply_to = message.get('reply_to_message')
            
            # Extract content (URLs mentioned in voice note)
            extracted = self.content_extractor.extract_all_content(
                transcription=transcription,
                reply_to_message=reply_to
            )
            
            # Process with unified AI
            ai_items = self._unified_ai_process(extracted)
            metadata = self._parse_input_metadata(transcription)
            
            entry_ids = []
            for ai_result in ai_items:
                entry_id = self._process_and_store(
                    content=ai_result['processed_content'],
                    content_type='audio' if len(entry_ids) == 0 else 'text',
                    file_path=persistent_path if len(entry_ids) == 0 else None,
                    is_content_idea=metadata['is_content_idea'] or ai_result['is_content_idea'],
                    output_types=metadata['output_types'],
                    category_hint=ai_result['category'],
                    subcategory_hint=ai_result.get('subcategory'),
                    title=ai_result['title'],
                    lock_entry_id=lock_entry_id if len(entry_ids) == 0 else None
                )
                entry_ids.append((entry_id, ai_result))
            
            # Build confirmation
            if len(entry_ids) == 1:
                entry_id, ai_result = entry_ids[0]
                confirmation = f"✅ Voice note processed! Entry ID: {entry_id}\n"
                
                if ai_result.get('intent') == 'trade_journal':
                    trade_msg = self._handle_trade_journal(ai_result)
                    confirmation += trade_msg
                
                confirmation += f"📁 Category: {ai_result['category']}\n"
                if ai_result['is_content_idea']:
                    confirmation += "💡 Marked as content idea\n"
                preview = ai_result['processed_content'][:250]
                if len(ai_result['processed_content']) > 250:
                    preview += "..."
                confirmation += f"\n📋 Content:\n{preview}"
            else:
                confirmation = f"✅ Created {len(entry_ids)} entries from voice note!\n\n"
                for i, (entry_id, ai_result) in enumerate(entry_ids, 1):
                    confirmation += f"{i}. {ai_result['title'][:40]} (ID: {entry_id})\n"
            
            self.send_message(chat_id, confirmation)
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}", exc_info=True)
            self.send_message(chat_id, f"❌ Error processing audio: {str(e)[:200]}")
    
    def _handle_video(self, chat_id: int, message: dict):
        """Handle video messages."""
        self.send_message(chat_id, "🎬 Processing video...")
        
        try:
            video = message['video']
            file_id = video['file_id']
            mime = video.get('mime_type', 'video/mp4')
            ext = '.' + mime.split('/')[-1] if '/' in mime else '.mp4'
            file_name = video.get('file_unique_id', file_id) + ext
            
            file_info = self.get_file(file_id)
            if not file_info:
                self.send_message(chat_id, "❌ Failed to get video from Telegram")
                return
            
            file_data = self.download_file(file_info['file_path'])
            if not file_data:
                self.send_message(chat_id, "❌ Failed to download video")
                return
            
            # Save file persistently
            filename = f"video/{file_id}_{file_name}"
            persistent_path = storage.save_file(file_data, filename, content_type=mime)
            
            if not persistent_path:
                persistent_path = "storage_failed"

            caption = message.get('caption', '')
            reply_to = message.get('reply_to_message')
            
            transcription = ""
            # DISABLED for Vercel performance - no video transcription
            # If enabled in future: use storage.save_temp() -> transcribe -> unlink
            
            # Extract content
            extracted = self.content_extractor.extract_all_content(
                text=caption,
                transcription=transcription,
                reply_to_message=reply_to
            )
            extracted['video_content'] = [{
                'path': persistent_path,
                'file_id': file_id,
                'transcription': transcription
            }]
            
            # Process with unified AI
            ai_items = self._unified_ai_process(extracted)
            metadata = self._parse_input_metadata(caption or transcription or "Video")
            
            entry_ids = []
            for ai_result in ai_items:
                entry_id = self._process_and_store(
                    content=ai_result['processed_content'],
                    content_type='video' if len(entry_ids) == 0 else 'text',
                    file_path=persistent_path if len(entry_ids) == 0 else None,
                    is_content_idea=metadata['is_content_idea'] or ai_result['is_content_idea'],
                    output_types=metadata['output_types'],
                    category_hint=ai_result['category'],
                    subcategory_hint=ai_result.get('subcategory'),
                    title=ai_result['title']
                )
                entry_ids.append((entry_id, ai_result))
            
            # Build confirmation
            if len(entry_ids) == 1:
                entry_id, ai_result = entry_ids[0]
                confirmation = f"✅ Video processed! Entry ID: {entry_id}\n"
                confirmation += f"📁 Category: {ai_result['category']}\n"
                preview = ai_result['processed_content'][:250]
                if len(ai_result['processed_content']) > 250:
                    preview += "..."
                confirmation += f"\n📋 Content:\n{preview}"
            else:
                confirmation = f"✅ Created {len(entry_ids)} entries from video!\n\n"
                for i, (entry_id, ai_result) in enumerate(entry_ids, 1):
                    confirmation += f"{i}. {ai_result['title'][:40]} (ID: {entry_id})\n"
            
            self.send_message(chat_id, confirmation)
            
        except Exception as e:
            logger.error(f"Video processing failed: {e}", exc_info=True)
            self.send_message(chat_id, f"❌ Error processing video: {str(e)[:200]}")
    
    def _handle_animation(self, chat_id: int, message: dict):
        """Handle GIF/animation messages."""
        self.send_message(chat_id, "🎞️ Processing GIF...")
        
        try:
            animation = message['animation']
            file_info = self.get_file(animation['file_id'])
            if not file_info:
                self.send_message(chat_id, "❌ Failed to get GIF from Telegram")
                return
            
            file_data = self.download_file(file_info['file_path'])
            if not file_data:
                self.send_message(chat_id, "❌ Failed to download GIF")
                return
            
            # Save to persistent storage
            timestamp = int(time.time())
            filename = f"images/{timestamp}_{animation['file_id']}.mp4"
            persistent_path = storage.save_file(file_data, filename, content_type='video/mp4')
            
            caption = message.get('caption', '')
            
            # Build extracted content
            extracted = {'text': caption or 'GIF Animation'}
            
            # Try image analysis on first frame
            try:
                image_analysis = self.ai_manager.analyze_image(file_data)
                extracted['image_analysis'] = image_analysis
            except Exception:
                pass
            
            # Process with unified AI
            ai_items = self._unified_ai_process(extracted)
            metadata = self._parse_input_metadata(caption) if caption else {
                'is_content_idea': False, 'output_types': [], 'clean_text': ''
            }
            
            entry_ids = []
            for ai_result in ai_items:
                entry_id = self._process_and_store(
                    content=ai_result['processed_content'],
                    content_type='video' if len(entry_ids) == 0 else 'text', # Animation/GIF = video
                    file_path=persistent_path if len(entry_ids) == 0 else None,
                    is_content_idea=metadata.get('is_content_idea', False) or ai_result['is_content_idea'],
                    output_types=metadata.get('output_types', []),
                    category_hint=ai_result['category'],
                    subcategory_hint=ai_result.get('subcategory'),
                    title=ai_result['title']
                )
                entry_ids.append((entry_id, ai_result))
            
            # Build confirmation
            if len(entry_ids) == 1:
                entry_id, ai_result = entry_ids[0]
                confirmation = f"✅ GIF analyzed! Entry ID: {entry_id}\n"
                confirmation += f"📁 Category: {ai_result['category']}\n"
                preview = ai_result['processed_content'][:400]
                if len(ai_result['processed_content']) > 400:
                    preview += "..."
                confirmation += f"\n📋 Analysis:\n{preview}"
            else:
                confirmation = f"✅ Created {len(entry_ids)} entries from GIF!\n\n"
                for i, (entry_id, ai_result) in enumerate(entry_ids, 1):
                    confirmation += f"{i}. {ai_result['title'][:40]} (ID: {entry_id})\n"
            
            self.send_message(chat_id, confirmation)
            
        except Exception as e:
            logger.error(f"Animation processing failed: {e}", exc_info=True)
            self.send_message(chat_id, f"❌ Error processing GIF: {str(e)[:200]}")
    
    def _handle_document(self, doc_data: dict, chat_id: int, caption: str = None) -> list:
        """Handle PDF and other documents."""
        try:
            file_id = doc_data['file_id']
            file_name = doc_data.get('file_name', 'document.pdf')
            mime_type = doc_data.get('mime_type', 'application/pdf')
            
            # Check for GIF/Video sent as file
            if mime_type == 'image/gif' or mime_type == 'video/mp4':
                # Treat as animation/video
                # But since we are here, just save it and process as document but without checking for PDF
                pass
            elif 'pdf' not in mime_type and not file_name.lower().endswith('.pdf'):
                self.send_message(chat_id, "⚠️ I mainly support PDF documents right now. I'll try to save this anyway.")
                # We can still save it, just maybe not extract text nicely
            
            # Get file path first
            file_info = self.get_file(file_id)
            if not file_info:
                self.send_message(chat_id, "❌ Failed to get document info from Telegram")
                return []
            
            # Download file
            file_data = self.download_file(file_info['file_path'])
            if not file_data:
                self.send_message(chat_id, "❌ Failed to download document")
                return []
            
            # Save persistent
            filename = f"documents/{file_id}_{file_name}"
            persistent_path = storage.save_file(file_data, filename, content_type=mime_type)
            
            if not persistent_path:
                persistent_path = "storage_failed"
            
            # Extract text from PDF using pypdf or similar?
            # For now, treat as a file attachment entry
            
            extracted = {
                'text': caption or f"Document: {file_name}",
                'document_content': [{
                    'path': persistent_path,
                    'file_id': file_id,
                    'filename': file_name
                }]
            }
            
            # Process with unified AI
            ai_items = self._unified_ai_process(extracted)
            metadata = self._parse_input_metadata(caption) if caption else {
                'is_content_idea': False, 'output_types': [], 'clean_text': ''
            }
            
            entry_ids = []
            for ai_result in ai_items:
                entry_id = self._process_and_store(
                    content=ai_result['processed_content'],
                    content_type='document' if len(entry_ids) == 0 else 'text',
                    file_path=persistent_path if len(entry_ids) == 0 else None,
                    is_content_idea=metadata.get('is_content_idea', False) or ai_result['is_content_idea'],
                    output_types=metadata.get('output_types', []),
                    category_hint=ai_result['category'],
                    subcategory_hint=ai_result.get('subcategory'),
                    title=ai_result['title']
                )
                entry_ids.append((entry_id, ai_result))
            
            # Build confirmation
            if len(entry_ids) == 1:
                entry_id, ai_result = entry_ids[0]
                confirmation = f"✅ Document processed! Entry ID: {entry_id}\n"
                confirmation += f"📁 Category: {ai_result['category']}\n"
                preview = ai_result['processed_content'][:400]
                if len(ai_result['processed_content']) > 400:
                    preview += "..."
                confirmation += f"\n📋 Analysis:\n{preview}"
            else:
                confirmation = f"✅ Created {len(entry_ids)} entries from document!\n\n"
                for i, (entry_id, ai_result) in enumerate(entry_ids, 1):
                    confirmation += f"{i}. {ai_result['title'][:40]} (ID: {entry_id})\n"
            
            self.send_message(chat_id, confirmation)
            
        except Exception as e:
            logger.error(f"Document handling error: {e}")
            self.send_message(chat_id, "❌ Valid document but processing failed.")
            return []

    # ========================================
    # AI Processing (reused from TelegramBot)
    # ========================================
    
    def _parse_input_metadata(self, text: str) -> Dict:
        """Parse input text for metadata hints."""
        text_lower = text.lower()
        
        is_content_idea = 'content idea' in text_lower or 'idea' in text_lower
        
        output_types = []
        if 'blog' in text_lower or 'article' in text_lower:
            output_types.append('blog')
        if 'youtube' in text_lower or 'video' in text_lower:
            output_types.append('youtube')
        if 'linkedin' in text_lower:
            output_types.append('linkedin')
        if 'shorts' in text_lower or 'reels' in text_lower or 'short' in text_lower:
            output_types.append('shorts')
        
        if 'all' in text_lower or (is_content_idea and not output_types):
            output_types = ['blog', 'youtube', 'linkedin', 'shorts', 'reels']
        
        clean_text = re.sub(
            r'\b(content idea|idea|for|blog|youtube|linkedin|shorts|reels|all)\b',
            '', text, flags=re.IGNORECASE
        )
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return {
            'is_content_idea': is_content_idea,
            'output_types': output_types,
            'clean_text': clean_text if clean_text else text
        }
    
    def _unified_ai_process(self, extracted_content: Dict[str, Any]) -> list:
        """
        Unified AI processing for ANY input combination.
        Mirror of TelegramBot._unified_ai_process but synchronous.
        """
        try:
            context_parts = []
            
            if extracted_content.get('text'):
                context_parts.append(f"USER MESSAGE: {extracted_content['text']}")
            
            if extracted_content.get('transcription'):
                context_parts.append(f"VOICE NOTE (transcribed): {extracted_content['transcription']}")
            
            for yt in extracted_content.get('youtube_content', []):
                context_parts.append(f"""YOUTUBE VIDEO:
- Title: {yt.get('title', 'Unknown')}
- Channel: {yt.get('channel', 'Unknown')}
- Duration: {yt.get('duration_seconds', 0) // 60} minutes
- URL: {yt.get('url', '')}""")
            
            for vid in extracted_content.get('video_platform_content', []):
                context_parts.append(f"""VIDEO ({vid.get('platform', 'Unknown')}):
- Title: {vid.get('title', 'Unknown')}
- Duration: {vid.get('duration_seconds', 0) // 60} minutes
- URL: {vid.get('url', '')}""")
            
            for url_data in extracted_content.get('url_content', []):
                context_parts.append(f"""WEB PAGE:
- URL: {url_data.get('url', '')}
- Title: {url_data.get('title', 'Unknown')}""")
            
            if extracted_content.get('image_analysis'):
                context_parts.append(f"IMAGE: {extracted_content['image_analysis']}")
            
            for img_analysis in extracted_content.get('image_url_analyses', []):
                context_parts.append(f"IMAGE FROM URL ANALYSIS: {img_analysis.get('analysis', '')}")
            
            if extracted_content.get('reply_context'):
                ctx = extracted_content['reply_context']
                context_parts.append(f"REPLYING TO MESSAGE: {ctx.get('text', '[media content]')}")
            
            full_context = "\n\n".join(context_parts)
            
            if not full_context.strip():
                return [{
                    'processed_content': 'No content to process',
                    'category': 'General Notes',
                    'is_content_idea': False,
                    'title': 'Empty Input',
                    'processing_note': 'No content extracted',
                    'intent': 'note'
                }]
            
            
            # Fetch dynamic categories
            all_cats = self.category_manager.get_all_categories()
            cat_list = [c['name'] for c in all_cats] if all_cats else []
            # Add defaults if missing
            defaults = ["Content Ideas", "VibeCoding Projects", "Stock Trading", "To-Do", "To Learn", "General Notes"]
            for d in defaults:
                if d not in cat_list:
                    cat_list.append(d)
            categories_str = ", ".join(cat_list)

            ai_prompt = f"""You are NexusLog Smart Logger. Analyze the input and respond in JSON.

INPUT CONTENT:
{full_context}

INSTRUCTIONS:
1. **NO SUMMARIZATION**: Do not summarize articles, videos, or external content.
2. **Text/Voice Notes**: Correct grammar, spelling, and formatting ONLY. Retain the original message length, tone, and details.
3. **Media/Links**: detailed log entry with the Title and Metadata. Do not hallucinate content you don't see.

**SPECIAL HANDLING**:
- **Content Ideas**: If the input sounds like a blog post, video idea, social media post, or business idea:
    - Set `is_content_idea` to true.
    - Set `category` to "Content Ideas".
- **Trading Journal**: If the input mentions "Trading Journal", "Trade", "Sold", "Bought" with a stock symbol (e.g., AAPL, TSLA) and/or date:
    - Set `intent` to "trade_journal".
    - Extract `date` (format: MM/DD/YYYY, default to today if "today" mentioned).
    - Extract `stock_symbol` (Ticker).
    - Content should be the commentary/lessons.
- **YouTube Education**: If a YouTube video is a tutorial, how-to, or educational, categorize as "Learn" (or "To Learn").

CATEGORIES: {categories_str}

Respond ONLY with valid JSON:
{{
  "items": [
    {{
      "intent": "note" | "trade_journal",
      "date": "MM/DD/YYYY",
      "stock_symbol": "SYMBOL",
      "title": "<Short descriptive title>",
      "processed_content": "<The corrected text OR metadata description>",
      "category": "<category>",
      "subcategory": "<subcategory (optional)>",
      "is_content_idea": true/false
    }}
  ]
}}"""
            
            ai_response = self.ai_manager.process_message(ai_prompt)
            
            default_item = {
                'processed_content': full_context[:500],
                'category': 'General Notes',
                'is_content_idea': False,
                'title': 'Untitled Entry',
                'processing_note': '',
                'intent': 'note'
            }
            
            if ai_response:
                try:
                    json_str = ai_response
                    if '```json' in json_str:
                        json_str = json_str.split('```json')[1].split('```')[0]
                    elif '```' in json_str:
                        json_str = json_str.split('```')[1].split('```')[0]
                    
                    ai_result = json.loads(json_str.strip())
                    
                    if 'items' in ai_result and isinstance(ai_result['items'], list):
                        items = []
                        for item in ai_result['items']:
                            items.append({
                                'processed_content': item.get('processed_content', default_item['processed_content']),
                                'category': item.get('category', 'General Notes'),
                                'is_content_idea': item.get('is_content_idea', False),
                                'title': item.get('title', default_item['title']),
                                'processing_note': item.get('processing_note', ''),
                                'intent': item.get('intent', 'note'),
                                'date': item.get('date'),
                                'stock_symbol': item.get('stock_symbol')
                            })
                        return items if items else [default_item]
                    
                    return [{
                        'processed_content': ai_result.get('processed_content', default_item['processed_content']),
                        'category': ai_result.get('category', 'General Notes'),
                        'is_content_idea': ai_result.get('is_content_idea', False),
                        'title': ai_result.get('title', default_item['title']),
                        'processing_note': ai_result.get('processing_note', ''),
                        'intent': ai_result.get('intent', 'note')
                    }]
                    
                except json.JSONDecodeError:
                    logger.warning("Failed to parse unified AI JSON response")
                    default_item['processed_content'] = ai_response[:1000]
            
            return [default_item]
            
        except Exception as e:
            logger.error(f"Unified AI processing error: {e}")
            return [{
                'processed_content': str(extracted_content)[:500],
                'category': 'General Notes',
                'is_content_idea': False,
                'title': 'Processing Error',
                'processing_note': f'Error: {str(e)[:100]}',
                'intent': 'note'
            }]
    
    # ========================================
    # DB Storage (reused from TelegramBot)
    # ========================================
    
    def _process_and_store(
        self,
        content: str,
        content_type: str,
        file_path: str = None,
        is_content_idea: bool = False,
        output_types: List[str] = None,
        category_hint: str = None,
        subcategory_hint: str = None,
        title: str = None,
        source_url: str = None,
        lock_entry_id: int = None
    ) -> int:
        """Process content and store in database. Returns entry ID."""
        session = get_session()
        try:
            # Get category suggestion
            if category_hint:
                category_info = self.category_manager.get_category_by_name(category_hint)
                if subcategory_hint and category_info.get('category_id'):
                    parent_id = category_info['category_id']
                    sub_cat = session.query(Category).filter(
                        Category.name == subcategory_hint,
                        Category.parent_id == parent_id
                    ).first()
                    if not sub_cat:
                        sub_cat = Category(
                            name=subcategory_hint,
                            parent_id=parent_id,
                            description="Auto-created by AI"
                        )
                        session.add(sub_cat)
                        session.flush()
                    category_info['subcategory_id'] = sub_cat.id
            else:
                category_info = self.category_manager.suggest_category(content)
            
            # Create or Update entry
            if lock_entry_id:
                entry = session.query(Entry).get(lock_entry_id)
                if entry:
                    entry.raw_content = content
                    entry.processed_content = content
                    entry.content_type = content_type
                    entry.file_path = file_path
                    entry.category_id = category_info.get('category_id')
                    entry.subcategory_id = category_info.get('subcategory_id')
                    # Merge metadata
                    new_meta = {
                        'is_content_idea': is_content_idea or category_info.get('is_content_idea', False),
                        'output_types': output_types or [],
                        'source_url': source_url,
                        # preserve existing metadata like file_unique_id
                    }
                    if entry.entry_metadata:
                        entry.entry_metadata.update(new_meta)
                    else:
                        entry.entry_metadata = new_meta
                else:
                    # Should unlikely happen if locked, but fallback to create
                    entry = Entry(
                        raw_content=content,
                        processed_content=content,
                        content_type=content_type,
                        file_path=file_path,
                        category_id=category_info.get('category_id'),
                        subcategory_id=category_info.get('subcategory_id'),
                        source='telegram',
                        entry_metadata={
                            'is_content_idea': is_content_idea or category_info.get('is_content_idea', False),
                            'output_types': output_types or [],
                            'source_url': source_url
                        }
                    )
                    session.add(entry)
            else:
                entry = Entry(
                    raw_content=content,
                    processed_content=content,
                    content_type=content_type,
                    file_path=file_path,
                    category_id=category_info.get('category_id'),
                    subcategory_id=category_info.get('subcategory_id'),
                    source='telegram',
                    entry_metadata={
                        'is_content_idea': is_content_idea or category_info.get('is_content_idea', False),
                        'output_types': output_types or [],
                        'source_url': source_url
                    }
                )
                session.add(entry)
        
            session.flush()
            
            # If it's a content idea, create ContentIdea entry
            if is_content_idea or category_info.get('is_content_idea'):
                ai_prompt = self.ai_manager.generate_content_prompt(content)
                idea_title = title or (content[:50] + '...' if len(content) > 50 else content)
                
                content_idea = ContentIdea(
                    entry_id=entry.id,
                    title=idea_title,
                    idea_description=content,
                    ai_prompt=ai_prompt,
                    output_types=output_types or ['blog', 'youtube', 'linkedin', 'shorts', 'reels'],
                    status='idea'
                )
                session.add(content_idea)
                session.flush()
                
                # Sync to Google Sheets
                if self.sheets:
                    try:
                        self.sheets.append_content_idea(content, ai_prompt, output_types or [])
                    except Exception as e:
                        logger.warning(f"Error syncing to Google Sheets: {e}")
            
            session.commit()
            return entry.id
        
        finally:
            session.close()
    
    # ========================================
    # Helper methods
    # ========================================
    
    def _build_text_confirmation(self, entry_ids: list, content_type: str) -> str:
        """Build a confirmation message for text processing results."""
        if not entry_ids:
            return "⚠️ No entries created."
        
        if len(entry_ids) == 1:
            entry_id, ai_result = entry_ids[0]
            confirmation = f"✅ Saved! Entry ID: {entry_id}\n"
            
            intent = ai_result.get('intent', 'note')
            if intent == "summary":
                confirmation += "📝 Summary created\n"
            elif intent == "analysis":
                confirmation += "🔍 Analysis complete\n"
            else:
                confirmation += "📝 Saved as note\n"
            
            if content_type == 'youtube':
                confirmation += "🎬 YouTube content processed\n"
            elif content_type == 'link':
                confirmation += "🔗 Link content extracted\n"
            
            if ai_result.get('category'):
                confirmation += f"📁 Category: {ai_result['category']}\n"
            
            if ai_result.get('is_content_idea'):
                confirmation += "💡 Marked as content idea\n"
            
            if ai_result.get('processing_note'):
                confirmation += f"\n🧠 AI: {ai_result['processing_note'][:150]}"
            
            preview = ai_result['processed_content'][:2000]
            if len(ai_result['processed_content']) > 2000:
                preview += "..."
            confirmation += f"\n\n📋 Content:\n{preview}"
        else:
            confirmation = f"✅ Created {len(entry_ids)} entries!\n\n"
            for i, (entry_id, ai_result) in enumerate(entry_ids, 1):
                confirmation += f"{i}. {ai_result['title'][:40]}\n"
                confirmation += f"   📁 {ai_result['category']}"
                if ai_result.get('is_content_idea'):
                    confirmation += " 💡"
                confirmation += f" (ID: {entry_id})\n\n"
        
        return confirmation
    
    def _handle_trade_journal(self, ai_result: dict) -> str:
        """Handle trading journal entries — sync to Google Sheets."""
        date = ai_result.get('date')
        stock = ai_result.get('stock_symbol')
        
        if not date or not stock:
            return "\n⚠️ Trade detected but Date/Stock missing for Sheet.\n"
        
        try:
            # Use the robust update logic
            sheets = SheetsIntegration()
            
            # Map content to commentary/lessons logic
            # For now, we put the whole content in 'commentary' (Col L)
            # If user splits it? AI prompt doesn't split it yet.
            # We'll just put processed_content into commentary.
            
            sheet_result = sheets.log_trade_journal(
                date=date,
                stock_symbol=stock,
                commentary=ai_result['processed_content'],
                lessons="" # AI doesn't split lessons yet, maybe future improvement
            )
            
            if sheet_result.get('success'):
                return f"\n{sheet_result['message']}\n"
            else:
                return f"\n{sheet_result.get('message', 'Unknown Error')}\n"
                
        except Exception as e:
            return f"\n⚠️ Sheet Handling Failed: {str(e)}\n"
