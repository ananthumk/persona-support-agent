import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from retry_utils import call_with_backoff

# Load environment variables (the API key) from .env
load_dotenv()


def classify_customer_persona(user_message: str) -> dict:
    """
    Analyzes the user's message and classifies it into one of three personas:
    Technical Expert, Frustrated User, or Business Executive.
    Returns a dictionary with persona, confidence, and reasoning.
    """
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

    system_instruction = (
        "You are an advanced classification engine. Your task is to analyze the "
        "sentiment, vocabulary, and tone of an incoming support message and classify "
        "it into exactly one of three customer personas:\n"
        "1. 'Technical Expert': Uses jargon, asks about APIs/code/configs.\n"
        "2. 'Frustrated User': Uses emotional language, exclamation marks, or mentions urgency.\n"
        "3. 'Business Executive': Focuses on business impact, ROI, timelines, and brevity.\n\n"
        "Provide your evaluation strictly in the requested JSON structure."
    )

    # This schema forces Gemini to reply in a strict, predictable JSON shape
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "persona": {
                "type": "STRING",
                "enum": ["Technical Expert", "Frustrated User", "Business Executive"]
            },
            "confidence": {"type": "NUMBER"},
            "reasoning": {"type": "STRING"}
        },
        "required": ["persona", "confidence", "reasoning"]
    }

    response = call_with_backoff(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.1
        )
    )

    return json.loads(response.text)


# This block only runs when you execute this file directly (python src/classifier.py)
# It will NOT run when this file is imported by other files later.
if __name__ == "__main__":
    test_messages = [
        "Our production API key stopped working with a 401 Unauthorized block. Check our logs immediately.",
        "This is the THIRD time I've had this problem! I need it fixed NOW, this is ridiculous!",
        "We need a clear timeline on when this billing issue resolves. It's affecting our quarterly reporting."
    ]

    for msg in test_messages:
        print(f"\nMessage: {msg}")
        result = classify_customer_persona(msg)
        print(json.dumps(result, indent=2))