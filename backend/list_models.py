"""List all available Gemini models"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv('GOOGLE_AI_API_KEY')
genai.configure(api_key=api_key)

print("=" * 80)
print("AVAILABLE GEMINI MODELS")
print("=" * 80)

for model in genai.list_models():
    # Only show models that support generateContent
    if 'generateContent' in model.supported_generation_methods:
        print(f"\n{model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Methods: {model.supported_generation_methods}")
