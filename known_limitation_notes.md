## Known Limitation: Semantic Gap in Retrieval Scoring

**Observed behavior:** During testing, the query "What HTTP status code should I expect on
an invalid bearer token?" correctly retrieved all top-3 chunks from `api_troubleshooting.md`
(the right document), but scored only 0.271 similarity — below our 0.30 confidence threshold.
This caused the system to escalate to a human even though the knowledge base actually
contained the correct answer (401 Unauthorized).

**Root cause:** The user's phrasing ("HTTP status code," "invalid bearer token") differs
lexically from the document's phrasing ("401 Unauthorized," "Missing or invalid authentication
token"). While both refer to the same concept, dense vector embeddings don't always score
synonymous-but-differently-worded queries as highly similar as a human reader would expect.
This is a known characteristic of embedding-based semantic search, not a defect in the
implementation.

**Why we did not "fix" this by lowering the threshold further:** Continuing to lower the
threshold to force this specific case to pass would reduce the system's ability to correctly
escalate genuinely low-confidence or out-of-scope queries elsewhere, trading one failure mode
for another rather than solving the underlying issue.

**How this is typically addressed in production RAG systems (beyond this assignment's scope):**
- Hybrid search (combining keyword/BM25 search with vector search)
- Query rewriting/expansion before embedding (e.g., using the LLM to rephrase the query
  using domain terminology before searching)
- Fine-tuning or selecting embedding models specifically benchmarked for the support domain
- Reranking retrieved candidates with a secondary, more context-aware model

**Conclusion:** The confidence threshold (0.30) was empirically tuned based on observed score
distributions from `gemini-embedding-001`, and the system's escalation-on-uncertainty design
means it fails safe (escalates to a human) rather than fails open (confidently hallucinates)
in these edge cases. This is the correct tradeoff for a customer support context.