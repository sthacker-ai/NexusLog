"""
Diagnostic: Check what's actually stored for YouTube entries
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from models import get_session, Entry

session = get_session()
try:
    # Get the most recent entries with content_type 'youtube' or containing 'youtube' in content
    entries = session.query(Entry).filter(
        (Entry.content_type == 'youtube') | 
        (Entry.raw_content.ilike('%youtube%')) |
        (Entry.processed_content.ilike('%youtube%'))
    ).order_by(Entry.id.desc()).limit(5).all()
    
    if not entries:
        print("NO YOUTUBE ENTRIES FOUND IN DATABASE")
    else:
        for e in entries:
            print(f"=== Entry ID: {e.id} ===")
            print(f"  content_type: '{e.content_type}'")
            print(f"  raw_content (first 300): '{(e.raw_content or '')[:300]}'")
            print(f"  processed_content (first 300): '{(e.processed_content or '')[:300]}'")
            print(f"  file_path: '{e.file_path}'")
            print(f"  metadata: {e.entry_metadata}")
            print(f"  created_at: {e.created_at}")
            
            # Check if ANY URL exists in the stored content
            import re
            urls_in_raw = re.findall(r'https?://[^\s]+', e.raw_content or '')
            urls_in_proc = re.findall(r'https?://[^\s]+', e.processed_content or '')
            print(f"  URLs found in raw_content: {urls_in_raw}")
            print(f"  URLs found in processed_content: {urls_in_proc}")
            print()
finally:
    session.close()
