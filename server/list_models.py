import sys
from google import genai
import json

api_key = sys.argv[1]
client = genai.Client(api_key=api_key)

print("🔍 Listing available models...")
try:
    models = client.models.list()
    for m in models:
        print(f"- {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")
