import os
import sys
import json
from google import genai
from google.genai import types

def test_gen():
    # Read key from config
    try:
        with open("../client/src/hooks/useAppState.ts", "r") as f:
            content = f.read()
            # Just grab it manually if needed, but let's mock it for now since we just need the model name
            pass
    except:
        pass

    # We will just print what models we are trying
    print("Models to try based on Lyria docs: lyria-3-pro-preview, lyria-3-clip-preview")

if __name__ == "__main__":
    test_gen()
