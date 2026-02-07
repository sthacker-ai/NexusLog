"""
NexusLog Telegram Bot Handler
Handles incoming messages from Telegram
"""
import os
import re
import time
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from models import Entry, ContentIdea, get_session
from ai_services import AIServiceManager
from category_manager import CategoryManager
from sheets_integration import SheetsIntegration
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logging - both console and file output
os.makedirs('logs', exist_ok=True)
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('logs/bot.log', mode='a', encoding='utf-8')  # File output
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables robustly
# 1. Try default loading
load_dotenv()

# 2. If essential var missing, try explicit parent path (for when running from backend dir)
if not os.getenv('TELEGRAM_BOT_TOKEN') or not os.getenv('GOOGLE_AI_API_KEY'):
    # backend/ -> NexusLog/.env
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(parent_env):
        logger.info(f"Loading .env from parent: {parent_env}")
        load_dotenv(parent_env)


class TelegramBot:
    """Telegram bot for NexusLog"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        
        self.ai_manager = AIServiceManager()
        self.category_manager = CategoryManager()
        
        try:
            self.sheets = SheetsIntegration()
            self.sheets.create_header_if_needed()
        except Exception as e:
            print(f"Google Sheets not configured: {e}")
            self.sheets = None
        
        self.app = Application.builder().token(self.token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup message handlers"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_image))
        self.app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self.handle_audio))
        self.app.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🧠 Welcome to NexusLog!

I'm your AI-powered idea logger. Send me:
- 📝 Text messages
- 🖼️ Images
- 🎤 Voice notes
- 🎥 Videos
- 🔗 Links

I'll process, categorize, and store everything for you!

Use /help to see all commands.
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 NexusLog Commands:

/start - Start the bot
/help - Show this help message

💡 How to use:
- Just send me any content!
- Add "content idea" to mark as content
- Specify output types: "blog", "youtube", "linkedin", "shorts", "reels"
- Example: "content idea for blog and youtube: How to build AI apps"

I'll automatically categorize and process everything! 🚀
        """
        await update.message.reply_text(help_text)
    
    def _parse_input_metadata(self, text: str) -> Dict:
        """
        Parse input text for metadata hints
        Returns: {
            'is_content_idea': bool,
            'output_types': list,
            'clean_text': str
        }
        """
        text_lower = text.lower()
        
        # Check if it's a content idea
        is_content_idea = 'content idea' in text_lower or 'idea' in text_lower
        
        # Extract output types
        output_types = []
        if 'blog' in text_lower or 'article' in text_lower:
            output_types.append('blog')
        if 'youtube' in text_lower or 'video' in text_lower:
            output_types.append('youtube')
        if 'linkedin' in text_lower:
            output_types.append('linkedin')
        if 'shorts' in text_lower or 'reels' in text_lower or 'short' in text_lower:
            output_types.append('shorts')
        
        # If "all" is mentioned or no specific type, default to all
        if 'all' in text_lower or (is_content_idea and not output_types):
            output_types = ['blog', 'youtube', 'linkedin', 'shorts', 'reels']
        
        # Clean the text (remove metadata hints)
        clean_text = re.sub(r'\b(content idea|idea|for|blog|youtube|linkedin|shorts|reels|all)\b', '', text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return {
            'is_content_idea': is_content_idea,
            'output_types': output_types,
            'clean_text': clean_text if clean_text else text
        }
    
    def _ai_process_text(self, text: str) -> list:
        """
        Shared AI processing for text content (used by both text and voice handlers).
        Returns LIST of dicts, each with: processed_content, category, is_content_idea, title, processing_note, intent
        Supports multi-item messages (e.g., "Add X to todo and Y as content idea")
        """
        try:
            # AI-first processing: intent detection, spell correction, multi-item parsing
            ai_prompt = f"""You are NexusLog AI assistant. Analyze this user message and respond in JSON format only.

User message: "{text}"

IMPORTANT: The user may mention MULTIPLE DISTINCT ITEMS in one message. For example:
- "Add 'review PRs' to todo and 'API patterns' as content idea" = 2 items
- "Remember to call mom, also got an idea for AI blog post" = 2 items  
- "Met John today for lunch" = 1 item

Determine:
1. How many DISTINCT items/notes are in this message? Parse each separately.

2. For EACH item determine:
   - INTENT: "note" (info to save) or "instruction" (action to perform)
   - Category: "Content Ideas", "VibeCoding Projects", "Stock Trading", "To-Do", or "General Notes"
   - Is it a content idea for blog/youtube/social?
   - A SHORT TITLE (max 50 chars)
   - Cleaned/corrected content

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "items": [
    {{
      "intent": "note" or "instruction",
      "title": "<short 5-10 word title>",
      "processed_content": "<cleaned note OR action result>",
      "category": "<suggested category>",
      "is_content_idea": true/false,
      "processing_note": "<brief note about what you did>"
    }}
  ]
}}

If single item, return array with 1 element. If multiple items, return array with each item."""

            ai_response = self.ai_manager.process_message(ai_prompt)
            
            # Default single item
            default_item = {
                'processed_content': text,
                'category': 'General Notes',
                'is_content_idea': False,
                'title': text[:50] + '...' if len(text) > 50 else text,
                'processing_note': '',
                'intent': 'note'
            }
            
            if ai_response:
                try:
                    # Parse JSON from response (handle markdown code blocks)
                    json_str = ai_response
                    if '```json' in json_str:
                        json_str = json_str.split('```json')[1].split('```')[0]
                    elif '```' in json_str:
                        json_str = json_str.split('```')[1].split('```')[0]
                    
                    ai_result = json.loads(json_str.strip())
                    
                    # Handle new multi-item format
                    if 'items' in ai_result and isinstance(ai_result['items'], list):
                        items = []
                        for item in ai_result['items']:
                            items.append({
                                'processed_content': item.get('processed_content', text),
                                'category': item.get('category', 'General Notes'),
                                'is_content_idea': item.get('is_content_idea', False),
                                'title': item.get('title', default_item['title']),
                                'processing_note': item.get('processing_note', ''),
                                'intent': item.get('intent', 'note')
                            })
                        return items if items else [default_item]
                    
                    # Backward compatibility with old single-item format
                    return [{
                        'processed_content': ai_result.get('processed_content', text),
                        'category': ai_result.get('category', 'General Notes'),
                        'is_content_idea': ai_result.get('is_content_idea', False),
                        'title': ai_result.get('title', default_item['title']),
                        'processing_note': ai_result.get('processing_note', ''),
                        'intent': ai_result.get('intent', 'note')
                    }]
                    
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI JSON, using raw response")
                    default_item['processed_content'] = ai_response
            
            return [default_item]
            
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return [{
                'processed_content': text,
                'category': 'General Notes',
                'is_content_idea': False,
                'title': text[:50] + '...' if len(text) > 50 else text,
                'processing_note': f'AI processing failed: {str(e)[:50]}',
                'intent': 'note'
            }]
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        AI-First text message handler with multi-item support.
        ALL messages go through AI for:
        1. Intent detection (note vs instruction)
        2. Multi-item parsing (single message -> multiple entries)
        3. Spell/grammar correction for notes
        4. URL detection and processing
        """
        text = update.message.text
        
        # URL detection regex
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        # Determine content type based on URL presence
        content_type = 'link' if urls else 'text'
        
        # Send processing indicator
        await update.message.reply_text("🧠 Processing with AI...")
        
        try:
            # Use shared AI processing method - now returns LIST
            ai_items = self._ai_process_text(text)
            
            # Parse metadata for output types (shared across all items)
            metadata = self._parse_input_metadata(text)
            
            entry_ids = []
            
            # Process each item
            for ai_result in ai_items:
                processed_content = ai_result['processed_content']
                category_hint = ai_result['category']
                is_content_idea = ai_result['is_content_idea']
                title = ai_result['title']
                
                # If URL present, prepend it to the first content only
                if urls and len(entry_ids) == 0:
                    if not any(url in processed_content for url in urls):
                        processed_content = f"Link: {urls[0]}\n\n{processed_content}"
                
                # Store entry
                entry_id = await self._process_and_store(
                    content=processed_content,
                    content_type=content_type if len(entry_ids) == 0 else 'text',
                    is_content_idea=metadata['is_content_idea'] or is_content_idea,
                    output_types=metadata['output_types'],
                    category_hint=category_hint,
                    title=title
                )
                entry_ids.append((entry_id, ai_result))
            
            # Build confirmation message
            if len(entry_ids) == 1:
                entry_id, ai_result = entry_ids[0]
                confirmation = f"✅ Saved! Entry ID: {entry_id}\n"
                
                if ai_result['intent'] == "instruction":
                    confirmation += "🤖 Executed as instruction\n"
                else:
                    confirmation += "📝 Saved as note\n"
                
                if content_type == 'link':
                    confirmation += f"🔗 Link detected\n"
                
                if ai_result['category']:
                    confirmation += f"📁 Category: {ai_result['category']}\n"
                
                if ai_result['is_content_idea']:
                    confirmation += "💡 Marked as content idea\n"
                
                if ai_result['processing_note']:
                    confirmation += f"\n🧠 AI: {ai_result['processing_note'][:150]}"
                
                # Show preview of processed content
                preview = ai_result['processed_content'][:200] + "..." if len(ai_result['processed_content']) > 200 else ai_result['processed_content']
                confirmation += f"\n\n📋 Content:\n{preview}"
            else:
                # Multi-item confirmation
                confirmation = f"✅ Created {len(entry_ids)} entries from your message!\n\n"
                for i, (entry_id, ai_result) in enumerate(entry_ids, 1):
                    confirmation += f"**{i}. {ai_result['title'][:40]}**\n"
                    confirmation += f"   📁 {ai_result['category']}"
                    if ai_result['is_content_idea']:
                        confirmation += " 💡"
                    confirmation += f" (ID: {entry_id})\n\n"
            
            await update.message.reply_text(confirmation)
            
        except Exception as e:
            logger.error(f"AI-first processing failed: {e}")
            # Fallback: save as-is
            metadata = self._parse_input_metadata(text)
            entry_id = await self._process_and_store(
                content=text,
                content_type=content_type,
                is_content_idea=metadata['is_content_idea'],
                output_types=metadata['output_types']
            )
            await update.message.reply_text(f"✅ Saved (without AI processing). Entry ID: {entry_id}")
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image messages"""
        photo = update.message.photo[-1]  # Get highest resolution
        file = await photo.get_file()
        
        # Download image
        file_path = f"uploads/images/{photo.file_id}.jpg"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        await file.download_to_drive(file_path)
        
        # OCR the image
        extracted_text = self.ai_manager.ocr_image(file_path)
        
        # Get caption if provided
        caption = update.message.caption or ""
        metadata = self._parse_input_metadata(caption) if caption else {'is_content_idea': False, 'output_types': [], 'clean_text': ''}
        
        # Combine caption and extracted text
        full_content = f"{metadata['clean_text']}\n\nExtracted from image:\n{extracted_text}"
        
        # Process and store
        entry_id = await self._process_and_store(
            content=full_content,
            content_type='image',
            file_path=file_path,
            is_content_idea=metadata['is_content_idea'],
            output_types=metadata['output_types']
        )
        
        await update.message.reply_text(f"✅ Image processed and saved! Entry ID: {entry_id}")
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle voice/audio messages with AI-first processing.
        Voice notes go through same AI processing as text:
        - Intent detection (note vs instruction)
        - Spell/grammar correction
        - Action execution if instruction
        """
        audio = update.message.voice or update.message.audio
        file = await audio.get_file()
        
        # Download audio
        file_path = f"uploads/audio/{audio.file_id}.ogg"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        await file.download_to_drive(file_path)
        
        # Transcribe
        await update.message.reply_text("🎙️ Transcribing voice note...")
        transcription = self.ai_manager.transcribe_audio(file_path)
        
        if not transcription:
            await update.message.reply_text("❌ Failed to transcribe voice note")
            return
        
        # AI-first processing of transcription
        await update.message.reply_text("🧠 Processing with AI...")
        ai_result = self._ai_process_text(transcription)
        
        # Parse metadata for output types
        metadata = self._parse_input_metadata(transcription)
        
        # Override is_content_idea if AI detected it
        if ai_result['is_content_idea']:
            metadata['is_content_idea'] = True
        
        # Process and store
        entry_id = await self._process_and_store(
            content=ai_result['processed_content'],
            content_type='audio',
            file_path=file_path,
            is_content_idea=metadata['is_content_idea'] or ai_result['is_content_idea'],
            output_types=metadata['output_types'],
            category_hint=ai_result['category'],
            title=ai_result['title']
        )
        
        # Build confirmation message
        confirmation = f"✅ Voice note saved! Entry ID: {entry_id}\n"
        
        if ai_result['intent'] == "instruction":
            confirmation += "🤖 Executed as instruction\n"
        else:
            confirmation += "📝 Saved as note\n"
        
        if ai_result['category']:
            confirmation += f"📁 Category: {ai_result['category']}\n"
        
        if ai_result['is_content_idea']:
            confirmation += "💡 Marked as content idea\n"
        
        if ai_result['processing_note']:
            confirmation += f"\n🧠 AI: {ai_result['processing_note'][:150]}"
        
        # Show preview
        preview = ai_result['processed_content'][:200] + "..." if len(ai_result['processed_content']) > 200 else ai_result['processed_content']
        confirmation += f"\n\n📋 Content:\n{preview}"
        
        await update.message.reply_text(confirmation)
        
        # Send Voice Confirmation (TTS) with processed content
        try:
            tts_text = f"I've processed your note: {ai_result['processed_content'][:200]}"
            audio_data = self.ai_manager.text_to_speech(tts_text)
            
            if audio_data:
                await update.message.reply_voice(audio_data, caption="🎙️ Voice confirmation")
            else:
                logger.warning("TTS generation returned empty data")
        except Exception as e:
            logger.error(f"Failed to send TTS response: {e}")
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages"""
        video = update.message.video
        file = await video.get_file()
        
        # Download video
        file_path = f"uploads/videos/{video.file_id}.mp4"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        await file.download_to_drive(file_path)
        
        # Transcribe
        transcription = self.ai_manager.transcribe_video(file_path)
        
        # Get caption if provided
        caption = update.message.caption or ""
        metadata = self._parse_input_metadata(caption) if caption else self._parse_input_metadata(transcription)
        
        # Process and store
        entry_id = await self._process_and_store(
            content=metadata['clean_text'],
            content_type='video',
            file_path=file_path,
            is_content_idea=metadata['is_content_idea'],
            output_types=metadata['output_types']
        )
        
        await update.message.reply_text(f"✅ Video processed and saved! Entry ID: {entry_id}")
    
    async def _process_and_store(
        self,
        content: str,
        content_type: str,
        file_path: str = None,
        is_content_idea: bool = False,
        output_types: List[str] = None,
        category_hint: str = None,
        title: str = None
    ) -> int:
        """Process content and store in database"""
        session = get_session()
        try:
            # Get category suggestion - prefer AI hint if provided
            if category_hint:
                # Use the AI-suggested category name to find ID
                category_info = self.category_manager.get_category_by_name(category_hint)
            else:
                category_info = self.category_manager.suggest_category(content)
            
            # Create entry
            entry = Entry(
                raw_content=content,
                processed_content=content,  # Already processed by AI
                content_type=content_type,
                file_path=file_path,
                category_id=category_info.get('category_id'),
                subcategory_id=category_info.get('subcategory_id'),
                source='telegram',
                entry_metadata={
                    'is_content_idea': is_content_idea or category_info.get('is_content_idea', False),
                    'output_types': output_types or []
                }
            )
            session.add(entry)
            session.flush()
            
            # If it's a content idea, create ContentIdea entry
            if is_content_idea or category_info.get('is_content_idea'):
                ai_prompt = self.ai_manager.generate_content_prompt(content)
                
                # Generate title if not provided
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
                        self.sheets.append_content_idea(
                            content,
                            ai_prompt,
                            output_types or []
                        )
                    except Exception as e:
                        print(f"Error syncing to Google Sheets: {e}")
            
            session.commit()
            return entry.id
        
        finally:
            session.close()
    
    def run(self):
        """Run the bot"""
        print("NexusLog Telegram Bot is running...")
        
        # Heartbeat loop in background
        import threading
        def heartbeat():
            while True:
                try:
                    with open('bot_heartbeat.txt', 'w') as f:
                        f.write(str(time.time()))
                except Exception as e:
                    logger.error(f"Heartbeat failed: {e}")
                time.sleep(60)
        
        threading.Thread(target=heartbeat, daemon=True).start()
        
        self.app.run_polling()
    
    def set_webhook(self, webhook_url: str):
        """Set webhook for production"""
        self.app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 8443)),
            url_path=self.token,
            webhook_url=f"{webhook_url}/{self.token}"
        )


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
