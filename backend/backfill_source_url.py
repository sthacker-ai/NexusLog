"""
Backfill existing YouTube entries with source_url in metadata.
This ensures the new frontend code can find URLs even for old entries.
"""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from models import get_session, Entry

session = get_session()
try:
    # Find all YouTube entries
    entries = session.query(Entry).filter(
        (Entry.content_type == 'youtube') | 
        (Entry.raw_content.ilike('%youtube.com%')) |
        (Entry.raw_content.ilike('%youtu.be%'))
    ).all()
    
    updated = 0
    for e in entries:
        meta = e.entry_metadata or {}
        if meta.get('source_url'):
            print(f"  Entry {e.id}: already has source_url, skipping")
            continue
        
        # Extract YouTube URL from content
        text = e.raw_content or e.processed_content or ''
        url_match = re.search(r'(https?://[^\s\)]+(?:youtube\.com|youtu\.be)[^\s\)]*)', text)
        if url_match:
            meta['source_url'] = url_match.group(1)
            e.entry_metadata = meta
            # Force SQLAlchemy to detect JSON change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(e, 'entry_metadata')
            updated += 1
            print(f"  Entry {e.id}: set source_url = {url_match.group(1)}")
        else:
            print(f"  Entry {e.id}: no YouTube URL found in content")
    
    session.commit()
    print(f"\nBackfilled {updated} entries with source_url")
finally:
    session.close()
