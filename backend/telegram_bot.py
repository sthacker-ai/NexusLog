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
    
    def _ai_process_text(self, text: str) -> dict:
        """
        Shared AI processing for text content (used by both text and voice handlers).
        Returns dict with: processed_content, category, is_content_idea, title, processing_note, intent
        """
        try:
            # AI-first processing: intent detection, spell correction, action execution
            ai_prompt = f"""You are NexusLog AI assistant. Analyze this user message and respond in JSON format only.

User message: "{text}"

Determine:
1. INTENT: Is this a DIRECT NOTE (information/thought to save) or an INSTRUCTION (action to perform)?
   - DIRECT NOTE examples: "Met John today", "idea for new app", "remember to buy milk"
   - INSTRUCTION examples: "summarize the news on budget", "check latest AI tools", "find info about X"

2. If DIRECT NOTE: Fix any spelling, grammar, improve formatting while keeping the meaning. Return clean version.

3. If INSTRUCTION: Extract what action is needed and execute it if possible. Return the result.

4. CATEGORY suggestion: "Content Ideas", "VibeCoding Projects", "Stock Trading", or "General Notes"

5. Is this a content idea for blog/youtube/social media?

6. Generate a SHORT TITLE (max 50 chars) that summarizes the content.

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "intent": "note" or "instruction",
  "title": "<short 5-10 word title>",
  "processed_content": "<cleaned note OR action result>",
  "category": "<suggested category>",
  "is_content_idea": true/false,
  "processing_note": "<brief note about what you did>"
}}"""

            ai_response = self.ai_manager.process_message(ai_prompt)
            
            # Default values
            result = {
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
                    
                    result['processed_content'] = ai_result.get('processed_content', text)
                    result['category'] = ai_result.get('category', 'General Notes')
                    result['is_content_idea'] = ai_result.get('is_content_idea', False)
                    result['title'] = ai_result.get('title', result['title'])
                    result['processing_note'] = ai_result.get('processing_note', '')
                    result['intent'] = ai_result.get('intent', 'note')
                    
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI JSON, using raw response")
                    result['processed_content'] = ai_response
            
            return result
            
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return {
                'processed_content': text,
                'category': 'General Notes',
                'is_content_idea': False,
                'title': text[:50] + '...' if len(text) > 50 else text,
                'processing_note': f'AI processing failed: {str(e)[:50]}',
                'intent': 'note'
            }
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        AI-First text message handler.
        ALL messages go through AI for:
        1. Intent detection (note vs instruction)
        2. Spell/grammar correction for notes
        3. Action execution for instructions
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
            # Use shared AI processing method
            ai_result = self._ai_process_text(text)
            
            processed_content = ai_result['processed_content']
            category_hint = ai_result['category']
            is_content_idea = ai_result['is_content_idea']
            processing_note = ai_result['processing_note']
            intent = ai_result['intent']
            title = ai_result['title']
            
            # If URL present, prepend it to the content
            if urls:
                if not any(url in processed_content for url in urls):
                    processed_content = f"Link: {urls[0]}\n\n{processed_content}"
            
            # Parse metadata for output types
            metadata = self._parse_input_metadata(text)
            
            # Override is_content_idea if AI detected it
            if is_content_idea:
                metadata['is_content_idea'] = True
            
            # Store entry
            entry_id = await self._process_and_store(
                content=processed_content,
                content_type=content_type,
                is_content_idea=metadata['is_content_idea'] or is_content_idea,
                output_types=metadata['output_types'],
                category_hint=category_hint,
                title=title
            )
            
            # Build confirmation message
            confirmation = f"✅ Saved! Entry ID: {entry_id}\n"
            
            if intent == "instruction":
                confirmation += "🤖 Executed as instruction\n"
            else:
                confirmation += "📝 Saved as note\n"
            
            if content_type == 'link':
                confirmation += f"🔗 Link detected\n"
            
            if category_hint:
                confirmation += f"📁 Category: {category_hint}\n"
            
            if is_content_idea:
                confirmation += "💡 Marked as content idea\n"
            
            if processing_note:
                confirmation += f"\n🧠 AI: {processing_note[:150]}"
            
            # Show preview of processed content
            preview = processed_content[:200] + "..." if len(processed_content) > 200 else processed_content
            confirmation += f"\n\n📋 Content:\n{preview}"
            
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
