import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key, default=None):
    """
    Get environment variable, checking for standard key and 'nl_' prefix (lowercase).
    Example: get_env('SECRET_KEY') checks 'SECRET_KEY' then 'nl_SECRET_KEY'.
    """
    val = os.getenv(key)
    if val is None:
        val = os.getenv(f'nl_{key}')
        
    # Also check if user used uppercase prefix just in case (NL_)
    if val is None:
        val = os.getenv(f'NL_{key}')
        
    if val is None:
        val = default
    return val
