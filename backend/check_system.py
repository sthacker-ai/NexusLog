import sys
import os
from dotenv import load_dotenv

# Ensure backend dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from health import get_system_status

def print_status():
    print("\n🔍 NexusLog System Diagnostic\n=============================")
    status = get_system_status()
    
    all_good = True
    
    for service, info in status.items():
        symbol = "✅" if info['status'] == 'online' else "❌"
        print(f"{symbol} {service.capitalize()}: {info['message']}")
        if info['status'] != 'online' and service not in ['ollama', 'replicate']: 
            # Replicate/Ollama might be optional
            if service == 'database' or service == 'gemini':
                all_good = False
    
    print("=============================")
    
    if all_good:
        print("🚀 System Ready! Launching services...")
        sys.exit(0)
    else:
        print("⚠️ Critical systems check failed or incomplete.")
        # We don't exit with error code to avoid blocking launch entirely if user wants to proceed
        # but we warn them.
        sys.exit(0) 

if __name__ == "__main__":
    print_status()
