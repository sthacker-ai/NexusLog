"""
NexusLog AI Services Layer
Modular abstraction for multiple AI providers
Priority: Gemini (free) → Ollama (local) → Replicate (fallback)
"""
import os
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import google.generativeai as genai
from models import get_session, UsageLog
import json
from datetime import datetime
from config import get_env


class AIServiceProvider(ABC):
    """Base class for AI service providers"""
    
    @abstractmethod
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file to text"""
        pass
    
    @abstractmethod
    def transcribe_video(self, video_path: str) -> str:
        """Transcribe video file to text"""
        pass
    
    @abstractmethod
    def ocr_image(self, image_path: str) -> str:
        """Extract text from image"""
        pass
    
    @abstractmethod
    def text_to_speech(self, text: str, voice: str = "en-GB-male") -> bytes:
        """Convert text to speech audio"""
        pass
    
    @abstractmethod
    def categorize_content(self, content: str, existing_categories: list) -> Dict[str, Any]:
        """Categorize content and suggest category"""
        pass
    
    @abstractmethod
    def generate_content_prompt(self, idea: str) -> str:
        """Generate a detailed prompt for content creation"""
        pass


class GeminiProvider(AIServiceProvider):
    """Google Gemini AI Provider (Primary - Free tier) with cascading model fallback"""
    
    # Model priority lists - try in order, fallback on rate limit (429) errors
    GENERAL_MODELS = [
        'gemini-3-flash-preview',      # Newest, may have best limits
        'gemini-2.5-flash',            # Stable 2.5
        'gemini-2.5-flash-preview-09-2025',  # Preview version
    ]
    IMAGE_MODEL = 'gemini-2.5-flash-image'  # For image generation
    TTS_MODEL = 'gemini-2.5-flash-preview-tts'  # For text-to-speech
    
    def __init__(self):
        # Use get_env to support nl_GOOGLE_AI_API_KEY
        api_key = get_env('GOOGLE_AI_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY not set")
        genai.configure(api_key=api_key)
        # Initialize with first general model; will cascade on errors
        self.current_model_index = 0
        self._init_model()
    
    def _init_model(self, model_name: str = None):
        """Initialize a specific model or the current one from the list"""
        # Set high output token limit to prevent truncation
        generation_config = {
            "max_output_tokens": 8192,
            "temperature": 0.2,
        }
        
        if model_name:
            self.model = genai.GenerativeModel(model_name, generation_config=generation_config)
        else:
            self.model = genai.GenerativeModel(self.GENERAL_MODELS[self.current_model_index], generation_config=generation_config)
        print(f"[Gemini] Using model: {self.model.model_name}")
    
    def _call_with_fallback(self, func, *args, **kwargs):
        """Execute a function with model fallback on rate limit errors"""
        last_error = None
        
        for i, model_name in enumerate(self.GENERAL_MODELS):
            try:
                self._init_model(model_name)
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                # Check for rate limit (429) or quota errors
                if '429' in error_str or 'quota' in error_str.lower() or 'rate' in error_str.lower():
                    print(f"[Gemini] Rate limit hit on {model_name}, trying next model...")
                    last_error = e
                    continue
                else:
                    # Non-rate-limit error, don't retry with different model
                    raise e
        
        # All models exhausted
        raise last_error if last_error else Exception("All Gemini models exhausted")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Gemini with model fallback"""
        # Validate file first (before any model calls)
        if not os.path.exists(audio_path):
            print(f"Audio file missing at: {audio_path}")
            return "Error: Audio file not found"
            
        file_size = os.path.getsize(audio_path)
        print(f"Uploading audio to Gemini: {audio_path} (Size: {file_size} bytes)")
        
        # Upload once, reuse across model attempts
        audio_file_obj = genai.upload_file(audio_path)
        print(f"Gemini file uri: {audio_file_obj.uri}")
        
        def _do_transcribe():
            prompt = "Transcribe this audio accurately. Only return the transcription, no additional commentary."
            response = self.model.generate_content([prompt, audio_file_obj])
            text = response.text.strip()
            log_usage('gemini', self.model.model_name, 'transcribe_audio', 
                      input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                      output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0)
            return text
        
        try:
            return self._call_with_fallback(_do_transcribe)
        except Exception as e:
            print(f"Gemini audio transcription error (all models failed): {e}")
            return ""
    
    def transcribe_video(self, video_path: str) -> str:
        """Transcribe video using Gemini with model fallback"""
        video_file_obj = genai.upload_file(video_path)
        
        def _do_transcribe():
            prompt = "Transcribe the audio from this video accurately. Only return the transcription, no additional commentary."
            response = self.model.generate_content([prompt, video_file_obj])
            text = response.text.strip()
            log_usage('gemini', self.model.model_name, 'transcribe_video', 
                      input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                      output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0)
            return text
        
        try:
            return self._call_with_fallback(_do_transcribe)
        except Exception as e:
            print(f"Gemini video transcription error (all models failed): {e}")
            return ""
    
    def ocr_image(self, image_path: str) -> str:
        """Extract text from image using Gemini Vision"""
        try:
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
            
            image_file_obj = genai.upload_file(image_path)
            
            prompt = "Extract all text from this image. If there's no text, describe the key ideas or concepts shown. Be concise."
            response = self.model.generate_content([prompt, image_file_obj])
            text = response.text.strip()
            
            # Log usage
            log_usage('gemini', self.model.model_name, 'ocr_image', 
                      input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                      output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0)
            
            return text
        except Exception as e:
            print(f"Gemini OCR error: {e}")
            return ""
    
    def analyze_image_vision(self, image_path: str, user_prompt: str = None) -> str:
        """
        Comprehensive image analysis using Gemini Vision.
        Can describe, OCR, or answer specific questions about the image.
        """
        image_file_obj = genai.upload_file(image_path)
        
        if user_prompt:
            prompt = f"""Analyze this image and respond to the user's request.
User's request: {user_prompt}
INSTRUCTIONS:
1. If user asks for "title" or "caption", provide a short 5-10 word description.
2. If user explicitly asks for "full details" or "OCR", provide it (but default is minimal)."""
        else:
            prompt = """Analyze this image and provide ONLY a short, descriptive title (5-10 words). 
Do not extract full text. Do not describe every detail. Just a title."""
        
        def _do_analyze():
            response = self.model.generate_content([prompt, image_file_obj])
            text = response.text.strip()
            # Debug log to see if model is truncating
            print(f"[Gemini Vision] Generated {len(text)} chars from image. Prompt: {user_prompt or 'default'}")
            
            log_usage('gemini', self.model.model_name, 'analyze_image_vision',
                      input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                      output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0)
            return text
        
        try:
            return self._call_with_fallback(_do_analyze)
        except Exception as e:
            print(f"Gemini image analysis error (all models failed): {e}")
            return ""
    
    def analyze_video_full(self, video_path_or_url: str, user_prompt: str = None) -> str:
        """
        Full video analysis using Gemini's native video understanding.
        Analyzes video quality, b-roll, visual effects, editing, etc.
        """
        import re
        
        # Check if it's a URL or local file
        if video_path_or_url.startswith('http'):
            youtube_pattern = r'(youtube\.com|youtu\.be)'
            if re.search(youtube_pattern, video_path_or_url):
                video_content = video_path_or_url
            else:
                return "Full video analysis currently supports YouTube URLs and local files only"
        else:
            video_content = genai.upload_file(video_path_or_url)
        
        if user_prompt:
            prompt = f"""Analyze this video based on the user's request: {user_prompt}"""
        else:
            prompt = """Analyze this video and provide ONLY a short, descriptive title (5-10 words).
Do not summarize the full content. Just generate a title."""
        
        def _do_analyze():
            response = self.model.generate_content([prompt, video_content])
            text = response.text.strip()
            log_usage('gemini', self.model.model_name, 'analyze_video_full',
                      input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                      output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0)
            return text
        
        try:
            return self._call_with_fallback(_do_analyze)
        except Exception as e:
            print(f"Gemini video analysis error (all models failed): {e}")
            return ""
    
    def text_to_speech(self, text: str, voice: str = "en-GB-male") -> bytes:
        """TTS using Gemini's TTS model (gemini-2.5-flash-preview-tts)"""
        try:
            # Use the dedicated TTS model
            tts_model = genai.GenerativeModel(self.TTS_MODEL)
            print(f"[Gemini TTS] Using model: {self.TTS_MODEL}")
            
            # Gemini TTS expects specific format - generate audio response
            response = tts_model.generate_content(
                f"Convert this text to natural speech: {text}",
                generation_config={"response_modalities": ["AUDIO"]}
            )
            
            # Extract audio bytes from response
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        audio_data = part.inline_data.data
                        mime_type = getattr(part.inline_data, 'mime_type', 'unknown')
                        print(f"[Gemini TTS] Got audio: {len(audio_data)} bytes, mime_type: {mime_type}")
                        
                        # Debug: Save to file for inspection
                        try:
                            debug_path = "uploads/debug_tts_output.audio"
                            os.makedirs("uploads", exist_ok=True)
                            with open(debug_path, 'wb') as f:
                                f.write(audio_data)
                            print(f"[Gemini TTS] Debug audio saved to: {debug_path}")
                        except OSError:
                             pass # Read-only FS on Vercel
                        
                        log_usage('gemini', self.TTS_MODEL, 'tts', input_tokens=len(text), output_tokens=0)
                        return audio_data
            
            print("[Gemini TTS] No audio data in response")
            print(f"[Gemini TTS] Response structure: {response}")
            return b""
        except Exception as e:
            error_str = str(e)
            print(f"Gemini TTS error: {e}")
            # Return empty to trigger fallback to Replicate
            return b""
    
    def categorize_content(self, content: str, existing_categories: list) -> Dict[str, Any]:
        """Categorize content intelligently with model fallback"""
        categories_str = ", ".join([cat['name'] for cat in existing_categories])
        
        prompt = f"""Analyze this content and categorize it.

Existing categories: {categories_str}

Content: {content}

Rules:
1. If it fits an existing category, use that category name
2. Only suggest a NEW category if absolutely necessary (we want max 10 categories total)
3. Determine if this is a content idea, coding project, stock trading idea, or general note
4. If it's a coding project, check if it belongs to an existing project subcategory

Respond in JSON format:
{{
    "category": "category name",
    "is_new_category": true/false,
    "subcategory": "subcategory name or null",
    "is_content_idea": true/false,
    "confidence": 0.0-1.0
}}"""
        
        def _do_categorize():
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            log_usage('gemini', self.model.model_name, 'categorize_content', 
                      input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                      output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0)
            return result
        
        try:
            return self._call_with_fallback(_do_categorize)
        except Exception as e:
            print(f"Gemini categorization error (all models failed): {e}")
            return {
                "category": "General Notes",
                "is_new_category": False,
                "subcategory": None,
                "is_content_idea": False,
                "confidence": 0.5
            }
    
    def generate_content_prompt(self, idea: str) -> str:
        """Generate a detailed prompt for content creation"""
        try:
            prompt = f"""You are a content strategist. Based on this idea, create a detailed prompt that could be used to write a full-length article or create a video.

Idea: {idea}

Create a comprehensive prompt that includes:
1. Main topic and angle
2. Target audience
3. Key points to cover
4. Tone and style
5. Call to action

Make it actionable and specific."""
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Log usage
            log_usage('gemini', self.model.model_name, 'generate_prompt', 
                      input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                      output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0)
            
            return text
        except Exception as e:
            print(f"Gemini prompt generation error: {e}")
            return f"Create content about: {idea}"


class OllamaProvider(AIServiceProvider):
    """Ollama Local AI Provider (Local - Free)"""
    
    def __init__(self):
        self.base_url = get_env('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = get_env('OLLAMA_MODEL', 'llama2')
    
    def _generate(self, prompt: str) -> str:
        """Generate text using Ollama"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return ""
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Ollama doesn't support audio transcription"""
        return ""
    
    def transcribe_video(self, video_path: str) -> str:
        """Ollama doesn't support video transcription"""
        return ""
    
    def ocr_image(self, image_path: str) -> str:
        """Ollama doesn't support image OCR natively"""
        return ""
    
    def text_to_speech(self, text: str, voice: str = "en-GB-male") -> bytes:
        """Ollama doesn't support TTS"""
        return b""
    
    def categorize_content(self, content: str, existing_categories: list) -> Dict[str, Any]:
        """Categorize content using Ollama"""
        try:
            categories_str = ", ".join([cat['name'] for cat in existing_categories])
            
            prompt = f"""Analyze this content and categorize it.

Existing categories: {categories_str}

Content: {content}

Respond ONLY with JSON (no markdown, no explanation):
{{
    "category": "category name",
    "is_new_category": true/false,
    "subcategory": null,
    "is_content_idea": true/false,
    "confidence": 0.8
}}"""
            
            response_text = self._generate(prompt)
            
            import json
            # Try to extract JSON
            if "{" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            
            return {
                "category": "General Notes",
                "is_new_category": False,
                "subcategory": None,
                "is_content_idea": False,
                "confidence": 0.5
            }
        except Exception as e:
            print(f"Ollama categorization error: {e}")
            return {
                "category": "General Notes",
                "is_new_category": False,
                "subcategory": None,
                "is_content_idea": False,
                "confidence": 0.5
            }
    
    def generate_content_prompt(self, idea: str) -> str:
        """Generate content prompt using Ollama"""
        prompt = f"Create a detailed content creation prompt for this idea: {idea}"
        return self._generate(prompt)


class ReplicateProvider(AIServiceProvider):
    """Replicate AI Provider (Fallback - uses google/gemini-3-flash and qwen/qwen3-tts)"""
    
    # Replicate model IDs
    GEMINI_MODEL = "google/gemini-3-flash"  # For general tasks
    TTS_MODEL = "qwen/qwen3-tts"  # For text-to-speech
    
    def __init__(self):
        self.api_key = get_env('REPLICATE_API_KEY')
        if not self.api_key:
            raise ValueError("REPLICATE_API_KEY not set")
        # Replicate library expects REPLICATE_API_TOKEN env var
        os.environ['REPLICATE_API_TOKEN'] = self.api_key
    
    def _run_gemini(self, prompt: str, image_url: str = None) -> str:
        """Run gemini-3-flash on Replicate"""
        try:
            import replicate
            input_data = {"prompt": prompt}
            if image_url:
                input_data["image"] = image_url
            
            output = replicate.run(self.GEMINI_MODEL, input=input_data)
            # Output is usually a generator or string
            if hasattr(output, '__iter__') and not isinstance(output, str):
                return "".join(output)
            return str(output) if output else ""
        except Exception as e:
            print(f"Replicate Gemini error: {e}")
            return ""
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Gemini-3-Flash on Replicate"""
        try:
            import replicate
            # Upload file and get URL
            with open(audio_path, 'rb') as f:
                # Replicate can accept file paths or URLs
                output = replicate.run(
                    "openai/whisper",  # Use Whisper for audio transcription
                    input={"audio": open(audio_path, 'rb')}
                )
            if output and 'transcription' in output:
                log_usage('replicate', 'openai/whisper', 'transcribe_audio', input_tokens=0, output_tokens=0)
                return output['transcription']
            return str(output) if output else ""
        except Exception as e:
            print(f"Replicate audio transcription error: {e}")
            return ""
    
    def transcribe_video(self, video_path: str) -> str:
        """Transcribe video using Replicate"""
        return ""
    
    def ocr_image(self, image_path: str) -> str:
        """OCR using Replicate Gemini"""
        return self._run_gemini(
            "Extract all text from this image. If there's no text, describe the key ideas.",
            image_url=image_path
        )
    
    # Jarvis-style voice description for TTS
    VOICE_DESCRIPTION = """A sophisticated male British AI assistant voice, similar to JARVIS from Iron Man. 
    The voice should be: calm, professional, and articulate with a slight warmth. 
    Speak at a measured pace, clear enunciation, with subtle confidence and helpfulness.
    British accent, middle-aged male, intelligent and formal but friendly."""
    
    def text_to_speech(self, text: str, voice: str = None) -> bytes:
        """TTS using Replicate Qwen3-TTS with Jarvis-style voice"""
        try:
            import replicate
            print(f"[Replicate TTS] Using model: {self.TTS_MODEL}")
            print(f"[Replicate TTS] Text length: {len(text)} chars")
            
            # Use voice design mode with the Jarvis description
            input_params = {
                "text": text,
                "mode": "voice_design",  # Creates voice from description
                "voice_description": self.VOICE_DESCRIPTION
            }
            
            output = replicate.run(self.TTS_MODEL, input=input_params)
            
            # Output is usually a URI. Download the audio bytes.
            if output:
                print(f"[Replicate TTS] Got output URL: {str(output)[:80]}...")
                response = requests.get(output)
                log_usage('replicate', self.TTS_MODEL, 'tts', input_tokens=len(text), output_tokens=0)
                print(f"[Replicate TTS] Downloaded audio: {len(response.content)} bytes")
                return response.content
            return b""
        except Exception as e:
            print(f"Replicate TTS error: {e}")
            return b""
    
    def categorize_content(self, content: str, existing_categories: list) -> Dict[str, Any]:
        """Categorize using Gemini-3-Flash on Replicate"""
        try:
            categories_str = ", ".join([cat['name'] for cat in existing_categories])
            prompt = f"""Analyze and categorize this content.
Existing categories: {categories_str}
Content: {content}

Respond ONLY with JSON:
{{"category": "category name", "is_new_category": true/false, "subcategory": null, "is_content_idea": true/false, "confidence": 0.8}}"""
            
            result_str = self._run_gemini(prompt)
            if result_str:
                # Parse JSON from response
                if "```json" in result_str:
                    result_str = result_str.split("```json")[1].split("```")[0].strip()
                elif "```" in result_str:
                    result_str = result_str.split("```")[1].split("```")[0].strip()
                
                return json.loads(result_str)
        except Exception as e:
            print(f"Replicate categorization error: {e}")
        
        return {
            "category": "General Notes",
            "is_new_category": False,
            "subcategory": None,
            "is_content_idea": False,
            "confidence": 0.5
        }
    
    def generate_content_prompt(self, idea: str) -> str:
        """Generate prompt using Replicate"""
        return f"Create content about: {idea}"


class AIServiceManager:
    """Manages AI service providers with fallback chain"""
    
    def __init__(self):
        self.providers = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers"""
        try:
            self.providers['gemini'] = GeminiProvider()
        except Exception as e:
            print(f"Gemini provider not available: {e}")
        
        try:
            self.providers['ollama'] = OllamaProvider()
        except Exception as e:
            print(f"Ollama provider not available: {e}")
        
        try:
            self.providers['replicate'] = ReplicateProvider()
        except Exception as e:
            print(f"Replicate provider not available: {e}")

def log_usage(provider: str, model: str, feature: str, input_tokens: int, output_tokens: int, details: Dict = None):
    """Log AI usage to database for cost tracking"""
    session = get_session()
    try:
        # Cost estimation logic (estimated costs if on paid tier)
        rate_input = 0.0
        rate_output = 0.0
        
        # Replicate Qwen3-TTS: $0.02 per 1,000 characters -> $0.00002 per char
        if provider == 'replicate' and feature == 'tts':
            rate_input = 0.00002 
        
        # Gemini 2.5 Flash (2025 pricing - free tier has no actual cost)
        # Input: $0.30 / 1M tokens ($0.0000003)
        # Output: $2.50 / 1M tokens ($0.0000025)
        if provider == 'gemini':
             rate_input = 0.0000003
             rate_output = 0.0000025

        cost = (input_tokens * rate_input) + (output_tokens * rate_output)
        
        log = UsageLog(
            provider=provider,
            model=model,
            feature=feature,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            details=details or {}
        )
        session.add(log)
        session.commit()
    except Exception as e:
        print(f"Failed to log usage: {e}")
    finally:
        session.close()

class AIServiceManager:
    """Manages AI service providers with fallback chain"""
    
    def __init__(self):
        self.providers = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers"""
        try:
            self.providers['gemini'] = GeminiProvider()
        except Exception as e:
            print(f"Gemini provider not available: {e}")
        
        try:
            self.providers['ollama'] = OllamaProvider()
        except Exception as e:
            print(f"Ollama provider not available: {e}")
        
        try:
            self.providers['replicate'] = ReplicateProvider()
        except Exception as e:
            print(f"Replicate provider not available: {e}")
    
    def get_provider(self, preferred: str = 'gemini') -> Optional[AIServiceProvider]:
        """Get AI provider with fallback"""
        # Try preferred provider
        if preferred in self.providers:
            return self.providers[preferred]
        
        # Fallback chain: gemini → ollama → replicate
        for provider_name in ['gemini', 'ollama', 'replicate']:
            if provider_name in self.providers:
                return self.providers[provider_name]
        
        return None
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio with fallback"""
        for provider_name in ['gemini', 'replicate']:
            if provider_name in self.providers:
                result = self.providers[provider_name].transcribe_audio(audio_path)
                if result:
                    return result
        return ""
    
    def transcribe_video(self, video_path: str) -> str:
        """Transcribe video with fallback"""
        for provider_name in ['gemini', 'replicate']:
            if provider_name in self.providers:
                result = self.providers[provider_name].transcribe_video(video_path)
                if result:
                    return result
        return ""
    
    def ocr_image(self, image_path: str) -> str:
        """OCR with fallback"""
        for provider_name in ['gemini', 'replicate']:
            if provider_name in self.providers:
                result = self.providers[provider_name].ocr_image(image_path)
                if result:
                    return result
        return ""
    
    def categorize_content(self, content: str, existing_categories: list) -> Dict[str, Any]:
        """Categorize with fallback"""
        for provider_name in ['gemini', 'ollama', 'replicate']:
            if provider_name in self.providers:
                result = self.providers[provider_name].categorize_content(content, existing_categories)
                if result and result.get('confidence', 0) > 0.3:
                    return result
        
        return {
            "category": "General Notes",
            "is_new_category": False,
            "subcategory": None,
            "is_content_idea": False,
            "confidence": 0.5
        }
    
    def text_to_speech(self, text: str, voice: str = "en-GB-male") -> bytes:
        """Text to speech - Uses Replicate Qwen TTS (Gemini TTS unreliable with deprecated SDK)"""
        # Note: Gemini TTS doesn't work reliably with the deprecated google.generativeai SDK
        # Using Qwen TTS on Replicate as primary provider
        if 'replicate' in self.providers:
            result = self.providers['replicate'].text_to_speech(text, voice)
            if result:
                print("[AIManager] TTS: Used Replicate Qwen")
                return result
            
        return b""

    def generate_content_prompt(self, idea: str) -> str:
        """Generate content prompt with fallback"""
        for provider_name in ['gemini', 'ollama', 'replicate']:
            if provider_name in self.providers:
                result = self.providers[provider_name].generate_content_prompt(idea)
                if result:
                    return result
        return f"Create content about: {idea}"

    def process_message(self, prompt: str) -> str:
        """
        Process any message with a custom prompt through AI.
        Use this for flexible AI tasks like intent detection, spell correction, 
        research requests, summarization, etc.
        """
        for provider_name in ['gemini', 'ollama', 'replicate']:
            if provider_name in self.providers:
                try:
                    provider = self.providers[provider_name]
                    if provider_name == 'gemini' and hasattr(provider, 'model'):
                        # Direct Gemini call
                        response = provider.model.generate_content(prompt)
                        result = response.text.strip()
                        if result:
                            # Log usage
                            from models import get_session, UsageLog
                            log_usage('gemini', provider.model.model_name, 'process_message',
                                      input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                                      output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0)
                            return result
                    elif provider_name == 'ollama':
                        # Ollama call
                        result = provider.generate_content(prompt) if hasattr(provider, 'generate_content') else provider._generate(prompt)
                        if result:
                            return result
                    elif provider_name == 'replicate':
                         # Replicate call logic if needed
                         pass
                except Exception as e:
                    print(f"AI process_message error with {provider_name}: {e}")
                    continue
        return ""

    def analyze_image_vision(self, image_path: str, user_prompt: str = None) -> str:
        """Analyze image with vision AI - centralized with fallback"""
        if 'gemini' in self.providers:
            result = self.providers['gemini'].analyze_image_vision(image_path, user_prompt)
            if result:
                return result
        # Fallback to basic OCR if vision analysis fails
        return self.ocr_image(image_path)
    
    def analyze_video_full(self, video_path_or_url: str, user_prompt: str = None) -> str:
        """Full video analysis with fallback"""
        if 'gemini' in self.providers:
            result = self.providers['gemini'].analyze_video_full(video_path_or_url, user_prompt)
            if result:
                return result
        return ""
