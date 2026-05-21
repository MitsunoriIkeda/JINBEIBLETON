import os
import sys
from google import genai
from google.genai import types

def test_gen():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    print("Testing Lyria audio generation...")
    try:
        response = client.models.generate_content(
            model='lyria-3-clip-preview',
            contents='Generate a 5 second drum beat',
            config={"response_modalities": ["AUDIO"]}
        )
        print(response)
        for part in response.candidates[0].content.parts:
            print("Part type:", type(part))
            if hasattr(part, 'text') and part.text:
                print("Text:", part.text)
            if hasattr(part, 'inline_data') and part.inline_data:
                print("Audio found!")
    except Exception as e:
        print("lyria-3-clip-preview failed:", e)
        
    print("\nTrying lyria-3-pro-preview...")
    try:
        response = client.models.generate_content(
            model='lyria-3-pro-preview',
            contents='Generate a 5 second drum beat',
            config={"response_modalities": ["AUDIO"]}
        )
        print("lyria-3-pro-preview success!")
    except Exception as e:
        print("lyria-3-pro-preview failed:", e)

if __name__ == "__main__":
    test_gen()
