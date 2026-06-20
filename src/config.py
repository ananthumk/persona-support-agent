# Centralized configuration values used across the project.
# Keeping these in one place means we only have to tune them in one spot.

# Minimum similarity score a retrieved chunk must have for the system
# to trust it enough to answer from it. Below this, we escalate to a human.
#
# NOTE: Empirically tuned to 0.30 (rather than the textbook default of 0.45)
# based on observed score ranges from the gemini-embedding-001 model during
# testing. Correct, on-topic matches scored between 0.20 and 0.43 in our
# testing, so 0.45 would have triggered escalation even on accurate answers.
CONFIDENCE_THRESHOLD = 0.30

# Number of top matching chunks to retrieve from the vector database per query.
TOP_K_RESULTS = 3

# Topics that should always be escalated to a human, regardless of
# retrieval confidence, because they carry legal/financial/account risk.
SENSITIVE_KEYWORDS = [
    "refund", "chargeback", "dispute", "legal", "lawsuit",
    "cancel my account", "delete my account", "fraud", "unauthorized charge"
]

GEMINI_GENERATION_MODEL = "gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"

MAX_RETRIES = 4