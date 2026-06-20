import os
from dotenv import load_dotenv
from google import genai

# Load the .env file so GEMINI_API_KEY becomes available
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No API key found. Check your .env file.")
else:
    print("API key loaded successfully. Calling Gemini now...")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say hello in exactly 5 words."
    )

    print("Gemini replied:")
    print(response.text)