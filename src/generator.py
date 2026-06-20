import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from config import GEMINI_GENERATION_MODEL
from escalator import should_escalate, generate_handoff_summary
from retry_utils import call_with_backoff

load_dotenv()


def build_persona_instructions(persona: str) -> str:
    """Returns the system prompt instructions matching the classified persona."""
    if persona == "Technical Expert":
        return (
            "You are a Senior Systems Engineer. Provide clear root-cause analysis, "
            "configuration specifications, and precise API pathways or code blocks. "
            "Keep technical descriptions exact and structured."
        )
    elif persona == "Frustrated User":
        return (
            "You are a deeply empathetic, reassuring Customer Care Specialist. "
            "Begin with a warm, genuine validation of their difficulty. Use straightforward, "
            "reassuring, and simple action-oriented bullet steps. Avoid confusing jargon."
        )
    else:  # Business Executive
        return (
            "You are a concise Client Relations Director. Focus on direct business outcomes, "
            "impact summaries, and timelines for resolution. Keep responses extremely "
            "brief, professional, and skip unnecessary configuration details."
        )


def generate_adaptive_response(user_query: str, persona: str, context_chunks: list) -> dict:
    """
    Main entry point: decides whether to escalate, and if not, generates a
    persona-styled response grounded ONLY in the retrieved context chunks.
    """
    # 1. Check escalation conditions FIRST, before spending an API call on generation
    if should_escalate(user_query, context_chunks):
        return {
            "escalated": True,
            "response": (
                "I apologize, but I am unable to confidently resolve this from our "
                "knowledge base, or this issue requires human review. I am connecting "
                "you with a live support specialist who can assist further."
            ),
            "handoff_summary": generate_handoff_summary(user_query, persona, context_chunks)
        }

    # 2. Build the persona-specific system prompt
    persona_instructions = build_persona_instructions(persona)

    context_text = "\n\n".join(
        [f"Source [{c['source']}]: {c['text']}" for c in context_chunks]
    )

    full_system_prompt = (
        f"{persona_instructions}\n\n"
        "CRITICAL RULES:\n"
        "- Base your response ONLY on the provided context.\n"
        "- Do not hallucinate or assume facts not found in the documents.\n"
        "- If the context doesn't fully answer the question, say so honestly.\n\n"
        f"FACTUAL CONTEXT DOCUMENTS:\n{context_text}"
    )

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

    response = call_with_backoff(
        client.models.generate_content,
        model=GEMINI_GENERATION_MODEL,
        contents=user_query,
        config=types.GenerateContentConfig(
            system_instruction=full_system_prompt,
            temperature=0.2
        )
    )

    return {
        "escalated": False,
        "response": response.text,
        "handoff_summary": None
    }


# Standalone test combining classifier + RAG + generator together.
# Run from project root: python src/generator.py
if __name__ == "__main__":
    from classifier import classify_customer_persona
    from rag_pipeline import LocalRAGPipeline

    pipeline = LocalRAGPipeline()

    test_messages = [
        "How do I reset my password? It's not letting me log in!",
        "What HTTP status code should I expect on an invalid bearer token?",
        "I demand a refund right now, I was charged twice this month!"
    ]

    for msg in test_messages:
        print("=" * 70)
        print(f"USER MESSAGE: {msg}")

        persona_result = classify_customer_persona(msg)
        persona = persona_result["persona"]
        print(f"DETECTED PERSONA: {persona}")

        context = pipeline.retrieve_context(msg, top_k=3)
        print(f"TOP RETRIEVAL SCORE: {max((c['score'] for c in context), default=0):.3f}")

        result = generate_adaptive_response(msg, persona, context)

        if result["escalated"]:
            print("\n>>> ESCALATED TO HUMAN <<<")
            print(result["response"])
            print("\nHandoff summary:")
            print(result["handoff_summary"])
        else:
            print("\nRESPONSE:")
            print(result["response"])
        print()