import json
from config import CONFIDENCE_THRESHOLD, SENSITIVE_KEYWORDS


def contains_sensitive_topic(user_query: str) -> bool:
    """Checks if the user's message mentions a topic we always want a human to handle."""
    lowered = user_query.lower()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


def should_escalate(user_query: str, context_chunks: list) -> bool:
    """
    Decides if a conversation should be escalated to a human, based on:
    1. Low retrieval confidence (best chunk score below threshold)
    2. No context chunks found at all
    3. Sensitive topic keywords detected in the query
    """
    if len(context_chunks) == 0:
        return True

    best_score = max(chunk["score"] for chunk in context_chunks)
    if best_score < CONFIDENCE_THRESHOLD:
        return True

    if contains_sensitive_topic(user_query):
        return True

    return False


def generate_handoff_summary(user_query: str, persona: str, context_chunks: list) -> str:
    """Builds a structured JSON report for the human agent taking over the conversation."""
    best_score = max((c["score"] for c in context_chunks), default=0.0)

    handoff_data = {
        "persona": persona,
        "detected_issue": user_query[:150] + ("..." if len(user_query) > 150 else ""),
        "retrieved_sources": [c["source"] for c in context_chunks],
        "confidence_score": round(best_score, 3),
        "sensitive_topic_flagged": contains_sensitive_topic(user_query),
        "recommended_action": (
            "Review retrieved sources for relevance, verify customer identity if account "
            "changes are involved, and respond directly given the low automated confidence "
            "or sensitive nature of this request."
        )
    }
    return json.dumps(handoff_data, indent=2)


# Quick standalone test: python src/escalator.py
if __name__ == "__main__":
    fake_chunks_good = [{"source": "password_reset_steps.txt", "score": 0.43}]
    fake_chunks_bad = [{"source": "billing_policy.txt", "score": 0.15}]

    print("Test 1 - Normal query, good confidence:")
    print(should_escalate("How do I reset my password?", fake_chunks_good))

    print("\nTest 2 - Low confidence:")
    print(should_escalate("How do I reset my password?", fake_chunks_bad))

    print("\nTest 3 - Sensitive keyword triggers escalation even with good confidence:")
    print(should_escalate("I demand a refund for this duplicate charge!", fake_chunks_good))

    print("\nTest 4 - Handoff summary example:")
    print(generate_handoff_summary(
        "I demand a refund for this duplicate charge!",
        "Frustrated User",
        fake_chunks_good
    ))