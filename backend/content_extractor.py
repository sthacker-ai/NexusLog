"""
NexusLog Content Extractor
Extracts content from various sources: YouTube, URLs, images, etc.
All AI calls are delegated to ai_services.py for centralized management.
"""
import os
import re
import logging
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Lazy import to avoid circular imports
_ai_manager = None

def get_ai_manager():
    """Get singleton AIServiceManager instance (lazy initialization)"""
    global _ai_manager
    if _ai_manager is None:
        from ai_services import AIServiceManager
        _ai_manager = AIServiceManager()
    return _ai_manager


class ContentExtractor:
    """
    Extracts content from various input types for unified AI processing.
    Supports: YouTube videos, generic URLs, images (vision), reply-to messages.
    
    All AI calls are delegated to AIServiceManager for centralized model management.
    """
    
    def __init__(self, ai_manager=None):
        """
        Initialize ContentExtractor.
        
        Args:
            ai_manager: Optional AIServiceManager instance. If not provided, 
                        uses singleton instance from ai_services.py
        """
        self.ai = ai_manager or get_ai_manager()
        logger.info("ContentExtractor initialized (using centralized AIServiceManager)")
    
    # =========================================================================
    # URL Detection
    # =========================================================================
    
    def detect_urls(self, text: str) -> Dict[str, list]:
        """
        Detect and categorize URLs in text.
        Returns: {'youtube': [...], 'video_platform': [...], 'image': [...], 'generic': [...]}
        """
        url_pattern = r'https?://[^\s<>\"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        youtube_pattern = r'(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)'
        
        result = {'youtube': [], 'video_platform': [], 'image': [], 'generic': []}
        for url in urls:
            if re.search(youtube_pattern, url):
                result['youtube'].append(url)
            elif self.is_image_url(url):
                result['image'].append(url)
            elif self.is_video_url(url):
                result['video_platform'].append(url)
            else:
                result['generic'].append(url)
        
        return result
    
    def is_image_url(self, url: str) -> bool:
        """
        Check if URL is a direct link to an image file.
        Detects common image extensions and media CDN patterns.
        """
        # Direct image extensions
        image_extensions = r'\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?.*)?$'
        if re.search(image_extensions, url.lower()):
            return True
        
        # Common image CDN patterns (Twitter, Instagram media, etc.)
        image_cdn_patterns = [
            r'pbs\.twimg\.com/media/',        # Twitter images
            r'instagram.*\.fbcdn\.net',       # Instagram images
            r'i\.imgur\.com/',                # Imgur
            r'media\.tenor\.com/',            # Tenor gifs
            r'cdn\.discordapp\.com/.*/.*\.(jpg|png|gif|webp)',  # Discord
        ]
        return any(re.search(pattern, url) for pattern in image_cdn_patterns)
    
    def extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    # =========================================================================
    # YouTube Content Extraction
    # =========================================================================
    
    def extract_youtube_content(self, url: str) -> Dict[str, Any]:
        """
        Extract content from YouTube video: title, description, transcript.
        Falls back to audio download + Gemini transcription if no captions available.
        """
        video_id = self.extract_youtube_video_id(url)
        if not video_id:
            return {'success': False, 'error': 'Invalid YouTube URL'}
        
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', 'Unknown Title')
                description = info.get('description', '')[:500]
                duration = info.get('duration', 0)
                channel = info.get('channel', 'Unknown Channel')
                
                # Try to get transcript with timestamps
                transcript = ""
                transcript_with_timestamps = []
                
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi
                    
                    # New API (v1.2+): use list_transcripts() + fetch()
                    ytt = YouTubeTranscriptApi()
                    transcript_list = ytt.fetch(video_id)
                    
                    # Store timestamps for later reference
                    for item in transcript_list:
                        timestamp_sec = int(item.start)
                        mins, secs = divmod(timestamp_sec, 60)
                        timestamp_str = f"{mins}:{secs:02d}"
                        transcript_with_timestamps.append({
                            'time': timestamp_str,
                            'seconds': timestamp_sec,
                            'text': item.text
                        })
                    
                    # transcript = " ".join([t.text for t in transcript_list])
                    # logger.info(f"YouTube transcript extracted: {len(transcript)} chars")
                    transcript = "" # Disabled for Smart Logger mode
                    
                except Exception as e:
                    logger.warning(f"YouTube transcript not available: {e}")
                    
                    # FALLBACK: Download audio and transcribe with Gemini
                    # transcript = self._transcribe_youtube_audio(url, video_id)
                    transcript = "" # Disabled for Smart Logger mode
                
                return {
                    'success': True,
                    'video_id': video_id,
                    'title': title,
                    'channel': channel,
                    'duration_seconds': duration,
                    'description': description,
                    'transcript': transcript[:8000] if transcript else "",
                    'timestamps': transcript_with_timestamps[:50],  # First 50 timestamps for reference
                    'url': url,
                    'source': 'youtube'
                }
                
        except Exception as e:
            logger.error(f"YouTube extraction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _transcribe_youtube_audio(self, url: str, video_id: str) -> str:
        """
        Download audio from YouTube and transcribe using Gemini.
        Used as fallback when no captions are available.
        """
        try:
            import yt_dlp
            import tempfile
            import os
            
            # Create temp file for audio
            audio_path = os.path.join(tempfile.gettempdir(), f"yt_audio_{video_id}.mp3")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestaudio/best',
                'outtmpl': audio_path.replace('.mp3', ''),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',  # Lower quality = smaller file = faster
                }],
            }
            
            logger.info(f"Downloading YouTube audio for transcription: {video_id}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Check if file exists (yt-dlp adds extension)
            if not os.path.exists(audio_path):
                audio_path = audio_path.replace('.mp3', '') + '.mp3'
            
            if os.path.exists(audio_path):
                # Transcribe using Gemini
                transcript = self._transcribe_audio_with_gemini(audio_path)
                
                # Clean up temp file
                try:
                    os.remove(audio_path)
                except:
                    pass
                
                return transcript
            else:
                logger.error("Audio file not found after download")
                return ""
                
        except Exception as e:
            logger.error(f"YouTube audio transcription failed: {e}")
            return ""
    
    def _transcribe_audio_with_gemini(self, audio_path: str) -> str:
        """Transcribe audio file using centralized AI service."""
        try:
            transcript = self.ai.transcribe_audio(audio_path)
            logger.info(f"Audio transcription: {len(transcript)} chars")
            return transcript
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return ""
    
    # =========================================================================
    # Generic URL Content Extraction
    # =========================================================================
    
    def extract_url_content(self, url: str) -> Dict[str, Any]:
        """
        Extract main content from a generic webpage.
        Uses trafilatura for content extraction.
        """
        try:
            import trafilatura
            
            # Download the page
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {'success': False, 'error': 'Failed to fetch URL'}
            
            # Extract main content
            content = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                include_links=False,
                output_format='txt'
            )
            
            # Filter out JavaScript blockers
            if content and any(p in content for p in ["JavaScript is not available", "Please enable JavaScript", "enable JavaScript to view"]):
                logger.warning(f"URL extraction blocked by JS check: {url}")
                content = ""
            
            # Also get metadata
            metadata = trafilatura.extract_metadata(downloaded)
            
            title = metadata.title if metadata else "Unknown Title"
            author = metadata.author if metadata else None
            date = metadata.date if metadata else None

            # Check for bad titles
            if title and "JavaScript is not available" in title:
                 title = "Unknown Title"
            
            # Special handling for X/Twitter
            if "x.com" in url or "twitter.com" in url:
                if title == "Unknown Title" or not title:
                    title = "X Post"
                if not content:
                    content = f"View original post on X: {url}"
            
            return {
                'success': True,
                'url': url,
                'title': title,
                'author': author,
                'date': date,
                'content': content[:5000] if content else "",  # Limit content length
            }
            
        except Exception as e:
            logger.error(f"URL extraction failed for {url}: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # Non-YouTube Video Extraction (Vimeo, Twitter, Instagram, etc.)
    # =========================================================================
    
    def is_video_url(self, url: str) -> bool:
        """
        Dynamically check if URL contains video content using yt-dlp.
        Works for any platform - Twitter, Vimeo, Instagram, etc.
        Returns True if the URL has extractable video content.
        """
        # Skip YouTube - handled separately with youtube-transcript-api
        youtube_pattern = r'(youtube\.com|youtu\.be)'
        if re.search(youtube_pattern, url):
            return False
        
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check if it has video content (duration > 0)
                if info and info.get('duration', 0) > 0:
                    logger.info(f"Video detected at {url}: {info.get('title', 'Unknown')} ({info.get('duration', 0)}s)")
                    return True
            
            return False
        except Exception as e:
            # If yt-dlp fails, it's not a video URL
            logger.debug(f"Not a video URL or extraction failed: {url} - {e}")
            return False
    
    def extract_video_content(self, url: str) -> Dict[str, Any]:
        """
        Extract content from non-YouTube video platforms.
        Downloads audio and transcribes with Gemini.
        """
        try:
            import yt_dlp
            import tempfile
            import hashlib
            
            # Create unique filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
            # storage_dir = "backend/static/uploads/videos"
            storage_dir = os.path.join("backend", "static", "uploads", "videos")
            os.makedirs(storage_dir, exist_ok=True)
            video_path = os.path.join(storage_dir, f"video_{url_hash}.mp4")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': video_path.replace('.mp4', ''),
            }
            
            logger.info(f"Downloading video from URL: {url}")
            
            # First get metadata without download
            with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown Video')
                duration = info.get('duration', 0)
                platform = info.get('extractor', 'Unknown')
            
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Check if file exists (yt-dlp adds extension sometimes, but we forced mp4 locally)
            # Actually yt-dlp might merge to .mp4
            if not os.path.exists(video_path):
                 # Try finding it
                 base = video_path.replace('.mp4', '')
                 for ext in ['.mp4', '.mkv', '.webm']:
                     if os.path.exists(base + ext):
                         video_path = base + ext
                         break
            
            transcript = "" # Disabled

            
            transcript = ""
            if os.path.exists(video_path):
                # transcript = self._transcribe_audio_with_gemini(audio_path)
                pass
            
            return {
                'success': True,
                'url': url,
                'title': title,
                'duration_seconds': duration,
                'platform': platform,
                'transcript': transcript[:8000] if transcript else "",
                'source': 'video_platform'
            }
            
        except Exception as e:
            logger.error(f"Video extraction failed for {url}: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # Full Video Analysis with centralized AI
    # =========================================================================
    
    def analyze_video_full(self, video_path_or_url: str, user_prompt: str = None) -> Dict[str, Any]:
        """
        Full video analysis using centralized AI service.
        Analyzes video quality, b-roll, visual effects, editing, etc.
        """
        try:
            analysis = self.ai.analyze_video_full(video_path_or_url, user_prompt)
            if analysis:
                return {
                    'success': True,
                    'analysis': analysis,
                    'source': video_path_or_url,
                    'analysis_type': 'full_video'
                }
            return {'success': False, 'error': 'Video analysis returned empty'}
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # Image Vision Analysis (not just OCR)
    # =========================================================================
    
    # Image Vision Analysis (not just OCR)
    # =========================================================================
    
    def _preprocess_image(self, image_path: str) -> str:
        """
        Upscale image if it's too small/low-res to help Vision AI read tiny text.
        Returns path to new image if processed, or original path if no change.
        """
        try:
            from PIL import Image
            
            # Check if we need to process
            should_process = False
            with Image.open(image_path) as img:
                width, height = img.size
                if width < 1600:
                    should_process = True
            
            if not should_process:
                return image_path
                
            # Re-open to process (to avoid issues with closed file context)
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Determine scale factor
                scale_factor = 2 if width < 800 else 1.5
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                # Limit max dimension
                if new_width > 3200:
                    ratio = 3200 / new_width
                    new_width = 3200
                    new_height = int(new_height * ratio)
                
                logger.info(f"Upscaling image for better OCR: {width}x{height} -> {new_width}x{new_height}")
                
                # High quality resampling
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save as PNG to temp dir
                import tempfile
                import os
                
                # Create new filename
                dir_name = os.path.dirname(image_path)
                base_name = os.path.basename(image_path)
                name, ext = os.path.splitext(base_name)
                new_filename = f"{name}_upscaled.png"
                new_path = os.path.join(dir_name, new_filename)
                
                img_resized.save(new_path, format='PNG')
                return new_path
                
        except ImportError:
            logger.warning("Pillow not installed, skipping image preprocessing")
            return image_path
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image_path

    def analyze_image(self, image_path: str, user_prompt: str = None) -> Dict[str, Any]:
        """
        Analyze image using centralized AI service.
        Can describe image, extract text, or answer specific questions.
        """
        try:
            # Preprocess to improve OCR (upscale if needed)
            processed_path = self._preprocess_image(image_path)
            
            analysis = self.ai.analyze_image_vision(processed_path, user_prompt)
            
            # Cleanup processed file if it's different from original
            if processed_path != image_path and os.path.exists(processed_path):
                try:
                    os.remove(processed_path)
                except:
                    pass
            
            if analysis:
                return {
                    'success': True,
                    'analysis': analysis,
                    'image_path': image_path,
                    'had_user_prompt': bool(user_prompt)
                }
            return {'success': False, 'error': 'Image analysis returned empty'}
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze_image_url(self, image_url: str, user_prompt: str = None) -> Dict[str, Any]:
        """
        Download and analyze a remote image URL.
        Downloads to temp, analyzes with vision AI, then cleans up.
        Automatically upgrades resolution for Twitter/X images.
        """
        try:
            import requests
            import tempfile
            import hashlib
            
            # Upgrade Twitter/X image resolution
            if 'pbs.twimg.com/media/' in image_url:
                if 'name=' in image_url:
                    # Replace name=small/medium/900x900 with name=orig for best quality
                    original_url = image_url
                    image_url = re.sub(r'name=[a-zA-Z0-9x_]+', 'name=orig', image_url)
                    if original_url != image_url:
                        logger.info(f"Upgraded Twitter image resolution: {image_url}")
                elif '?' in image_url:
                    image_url += '&name=orig'
                else:
                    image_url += '?format=jpg&name=orig'
            
            # Download image
            response = requests.get(image_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            # Determine extension from content type or URL
            content_type = response.headers.get('content-type', 'image/png')
            ext = '.png'
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'webp' in content_type:
                ext = '.webp'
            
            # Save to backend/static/uploads/images
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:10]
            # storage_dir = "backend/static/uploads/images"
            storage_dir = os.path.join("backend", "static", "uploads", "images")
            os.makedirs(storage_dir, exist_ok=True)
            temp_path = os.path.join(storage_dir, f"img_{url_hash}{ext}")
            
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded image from URL: {len(response.content)} bytes")
            
            # Analyze with vision (handles preprocessing internally)
            result = self.analyze_image(temp_path, user_prompt)
            
            # Clean up original download - DISABLED to persist file
            # try:
            #     if os.path.exists(temp_path):
            #         os.remove(temp_path)
            # except:
            #     pass
            
            if result['success']:
                result['source_url'] = image_url
            
            # Return relative path for frontend if saved to static
            if "backend/static" in temp_path:
                 # result['local_path'] = temp_path # Store full path
                 pass

            return result
            
        except Exception as e:
            logger.error(f"Image URL analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # Reply-to Message Handling
    # =========================================================================
    
    def get_reply_context(self, reply_to_message) -> Optional[Dict[str, Any]]:
        """
        Extract content from a replied-to Telegram message.
        Returns context about the original message.
        """
        if not reply_to_message:
            return None
        
        context = {
            'message_id': reply_to_message.message_id,
            'text': reply_to_message.text or reply_to_message.caption or "",
            'has_photo': bool(reply_to_message.photo),
            'has_video': bool(reply_to_message.video),
            'has_voice': bool(reply_to_message.voice),
            'has_document': bool(reply_to_message.document),
        }
        
        return context
    
    # =========================================================================
    # Unified Content Extraction
    # =========================================================================
    
    def extract_all_content(
        self,
        text: str = None,
        transcription: str = None,
        image_path: str = None,
        video_path: str = None,
        reply_to_message = None
    ) -> Dict[str, Any]:
        """
        Extract content from all provided inputs and return unified context.
        This is the main entry point for the unified processor.
        
        Returns a dict with all extracted content ready for AI processing.
        """
        result = {
            'text': text or "",
            'transcription': transcription or "",
            'urls': {'youtube': [], 'video_platform': [], 'image': [], 'generic': []},
            'youtube_content': [],
            'video_platform_content': [],
            'url_content': [],
            'image_analysis': None,
            'image_url_analyses': [],  # New: for multiple image URLs
            'reply_context': None,
            'extraction_notes': []
        }
        
        # Detect URLs in text or transcription
        combined_text = f"{text or ''} {transcription or ''}"
        if combined_text.strip():
            result['urls'] = self.detect_urls(combined_text)
            
            # Extract YouTube content
            for yt_url in result['urls']['youtube']:
                yt_content = self.extract_youtube_content(yt_url)
                if yt_content['success']:
                    result['youtube_content'].append(yt_content)
                    result['extraction_notes'].append(f"Extracted YouTube: {yt_content['title']}")
                else:
                    result['extraction_notes'].append(f"YouTube extraction failed: {yt_content.get('error')}")
            
            # Extract non-YouTube video platform content (Vimeo, Twitter videos, etc.)
            for vid_url in result['urls']['video_platform']:
                vid_content = self.extract_video_content(vid_url)
                if vid_content['success']:
                    result['video_platform_content'].append(vid_content)
                    result['extraction_notes'].append(f"Extracted video: {vid_content['title']} ({vid_content['platform']})")
                # Note: Don't log failures for video detection as it's expected for non-video URLs
            
            # Analyze image URLs with vision AI
            user_prompt_for_images = None
            if combined_text.strip():
                # Remove URLs from text to get just the user's request
                clean_text = re.sub(r'https?://[^\s]+', '', combined_text).strip()
                if clean_text:
                    user_prompt_for_images = clean_text
            
            for img_url in result['urls']['image']:
                img_result = self.analyze_image_url(img_url, user_prompt_for_images)
                if img_result['success']:
                    result['image_url_analyses'].append(img_result)
                    result['extraction_notes'].append(f"Analyzed image from URL")
                else:
                    result['extraction_notes'].append(f"Image URL analysis failed: {img_result.get('error')}")
            
            # Extract generic URL content (articles, webpages)
            for url in result['urls']['generic']:
                url_content = self.extract_url_content(url)
                if url_content['success']:
                    result['url_content'].append(url_content)
                    result['extraction_notes'].append(f"Extracted URL: {url_content['title']}")
        
        # Analyze image if provided
        if image_path:
            # Use text/transcription as user prompt if it seems like a question
            user_prompt = None
            if combined_text.strip():
                question_indicators = ['?', 'what', 'how', 'why', 'summarize', 'extract', 'describe', 'analyze', 'tell me']
                if any(ind in combined_text.lower() for ind in question_indicators):
                    user_prompt = combined_text.strip()
            
            image_result = self.analyze_image(image_path, user_prompt)
            if image_result['success']:
                result['image_analysis'] = image_result['analysis']
                result['extraction_notes'].append("Image analyzed with vision")
            else:
                result['extraction_notes'].append(f"Image analysis failed: {image_result.get('error')}")
        
        # Get reply context
        if reply_to_message:
            result['reply_context'] = self.get_reply_context(reply_to_message)
            if result['reply_context']:
                result['extraction_notes'].append("Reply context captured")
        
        return result


# Singleton instance for import
_extractor = None

def get_content_extractor() -> ContentExtractor:
    """Get singleton ContentExtractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = ContentExtractor()
    return _extractor
