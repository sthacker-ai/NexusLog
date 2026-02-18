import os
import requests
import mimetypes
import tempfile
import shutil
from pathlib import Path

from config import get_env

class FileStorage:
    def __init__(self):
        self.mode = get_env('STORAGE_MODE', 'local').lower()
        # Support standard, NL_ prefix, and user's specific nl_READ_WRITE_TOKEN
        self.blob_token = get_env('BLOB_READ_WRITE_TOKEN') or get_env('READ_WRITE_TOKEN')
        
        self.upload_dir = Path('static/uploads')
        self.is_readonly = False
        
        # Only attempt to create local directories if we are in local mode OR if we just want to try
        # But to avoid Vercel crash, we wrap in try/except 
        try:
            if self.mode == 'local':
                self.upload_dir.mkdir(parents=True, exist_ok=True)
                (self.upload_dir / 'images').mkdir(exist_ok=True)
                (self.upload_dir / 'audio').mkdir(exist_ok=True)
                (self.upload_dir / 'video').mkdir(exist_ok=True)
                (self.upload_dir / 'documents').mkdir(exist_ok=True)
        except OSError:
            # Vercel Read-Only FS
            print("Warning: Read-only filesystem, local uploads disabled.")
            self.is_readonly = True
            if self.mode == 'local':
                 print("CRITICAL: STORAGE_MODE is local but filesystem is read-only. File uploads will fail.")

    def save_file(self, file_data: bytes, filename: str, content_type: str = None) -> str:
        """
        Save file and return the URL/path.
        
        Args:
            file_data: Bytes of the file
            filename: Target filename (e.g., 'images/photo.jpg')
            content_type: MIME type of the file
            
        Returns:
            str: Public URL (if blob) or relative path (if local). Returns None if save failed.
        """
        if self.mode == 'vercel_blob':
            return self._save_to_vercel_blob(file_data, filename, content_type)
        else:
            return self._save_to_local(file_data, filename)

    def save_temp(self, file_data: bytes, suffix: str = None) -> str:
        """
        Save to a temporary file in the system temp directory (always writable).
        Useful for processing (audios/videos) before permanent storage.
        Caller is responsible for cleaning up if needed, though OS usually handles /tmp.
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_data)
                return tmp.name
        except Exception as e:
            print(f"Error saving temp file: {e}")
            return None

    def _save_to_local(self, file_data: bytes, filename: str) -> str:
        if self.is_readonly:
            print(f"Cannot save {filename}: Filesystem is read-only.")
            return None
            
        try:
            # Ensure directory exists for nested filenames
            target_path = self.upload_dir / filename
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'wb') as f:
                f.write(file_data)
                
            # Return path relative to static/
            return str(Path('static/uploads') / filename).replace('\\', '/')
        except Exception as e:
            print(f"Local save error: {e}")
            return None

    def _save_to_vercel_blob(self, file_data: bytes, filename: str, content_type: str) -> str:
        if not self.blob_token:
            print("Warning: BLOB_READ_WRITE_TOKEN not set, falling back to local")
            return self._save_to_local(file_data, filename)

        try:
            import vercel_blob
            # vercel_blob.put returns a dictionary with 'url'
            # options={'access': 'public', 'token': self.blob_token} if token not in env
            # The library usually picks up BLOB_READ_WRITE_TOKEN env var.
            # Passing token explicitly to be safe if we use NL_ prefix.
            
            resp = vercel_blob.put(
                filename, 
                file_data, 
                options={
                    'access': 'public', 
                    'contentType': content_type,
                    'token': self.blob_token
                }
            )
            return resp.get('url')

        except ImportError:
            print("vercel-blob library not found. Falling back to local.")
            return self._save_to_local(file_data, filename)
        except Exception as e:
            print(f"Vercel Blob upload failed: {e}")
            # Do NOT fallback to local if we wanted blob, effectively fail rather than crash
            return None

# Singleton instance
storage = FileStorage()
