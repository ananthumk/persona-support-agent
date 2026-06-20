# Persona-Adaptive Customer Support Agent

An intelligent customer support chatbot that classifies a user's communication
style (Technical Expert, Frustrated User, or Business Executive) and adapts
its response tone accordingly, using Retrieval-Augmented Generation (RAG) to
answer only from a local knowledge base. Low-confidence or sensitive queries
are automatically escalated to a human agent with a structured handoff report.

## Architecture

```
[User Message] --> [Persona Classifier] --> [Persona Tag: Tech/Frustrated/Exec]
                        |
                        v
                [Vector Database] --> [Cosine Similarity Search] --> [Top-K Chunks]
                        |
                        v
            [Adaptive Prompt Engine] --> (Retrieval Quality Check)
                        |                                  |
                        | (Sufficient Info Found)          | (Confidence Low / Sensitive Issue)
                        v                                  v
             [Generate Adaptive Response]         [Escalate to Human Agent]
                                                           |
                                                           v
                                                [Generate Handoff JSON]
```

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.13 | Core language |
| Google Gemini API (`gemini-2.5-flash`) | Persona classification and response generation |
| Gemini Embeddings (`gemini-embedding-001`) | Converts text into vector embeddings for semantic search |
| ChromaDB | Local vector database for storing and searching document embeddings |
| LangChain (`langchain-text-splitters`) | Recursive text chunking for document ingestion |
| pypdf | Extracts text from PDF knowledge base documents |
| Streamlit | Web-based chat interface |
| python-dotenv | Secure API key management via `.env` |

**Note on model names:** This project originally referenced
`gemini-2.5-flash-preview-09-2025` and `text-embedding-004`. Both were found
to be deprecated/removed during development (verified June 2026) and were
replaced with `gemini-2.5-flash` and `gemini-embedding-001`, the current
stable equivalents.

## Setup Instructions

1. Clone/download this repository and open it in VS Code.
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Get a Gemini API key from https://aistudio.google.com/app/apikey
5. Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY="your_actual_key_here"
   ```
6. Ingest the knowledge base (run once, or after editing files in `data/`):
   ```
   python src/rag_pipeline.py
   ```
7. Launch the app:
   ```
   streamlit run app.py
   ```

## Project Structure

```
persona-support-agent/
├── data/                          <- Knowledge base source documents
│   ├── api_troubleshooting.md
│   ├── billing_policy.txt
│   ├── general_support_guide.pdf
│   └── password_reset_steps.txt
├── src/
│   ├── config.py                  <- Thresholds, model names, sensitive keywords
│   ├── classifier.py              <- Persona detection
│   ├── rag_pipeline.py            <- Chunking, embedding, vector search
│   ├── generator.py                <- Persona-adaptive response generation
│   ├── escalator.py                <- Escalation logic + handoff JSON
│   └── retry_utils.py              <- Exponential backoff for transient API errors
├── app.py                          <- Streamlit chat UI
├── requirements.txt
├── .env                            <- Not committed; holds API key
└── README.md
```

## How It Works

1. **Classification** — each message is sent to Gemini with a structured
   JSON schema, returning `persona`, `confidence`, and `reasoning`.
2. **Retrieval** — the message is embedded and compared via cosine
   similarity against pre-embedded chunks of the knowledge base stored in
   ChromaDB. The top-3 most similar chunks are returned.
3. **Escalation check** — before generating a response, the system checks
   whether the best retrieval score is below the 0.30 confidence threshold,
   or whether the message contains a sensitive keyword (refund, legal,
   delete account, etc.). If either is true, the conversation escalates and
   a JSON handoff summary is generated instead of an AI-written answer.
4. **Generation** — if not escalated, the retrieved chunks and persona are
   combined into a system prompt instructing Gemini to answer strictly from
   the provided context, in a tone matching the detected persona.

## Known Limitations

### 1. Confidence threshold tuning

The original spec suggested a 0.45 cosine similarity threshold for
escalation. During testing, correct/on-topic retrieval matches scored
between 0.18 and 0.43 using `gemini-embedding-001`, meaning 0.45 would have
escalated almost every query, including accurate ones. The threshold was
empirically lowered to **0.30** based on observed score distributions.

### 2. Semantic gap in retrieval scoring

**Observed behavior:** The query "What HTTP status code should I expect on
an invalid bearer token?" correctly retrieved all top-3 chunks from
`api_troubleshooting.md` (the right document), but scored only 0.271
similarity — below the 0.30 confidence threshold. This caused escalation
even though the knowledge base contained the correct answer (401
Unauthorized).

**Root cause:** The user's phrasing ("HTTP status code," "invalid bearer
token") differs lexically from the document's phrasing ("401 Unauthorized,"
"Missing or invalid authentication token"). Dense vector embeddings don't
always score synonymous-but-differently-worded queries as highly similar as
a human reader would expect. This is a known characteristic of
embedding-based semantic search, not a defect in this implementation.

**Why this wasn't "fixed" by lowering the threshold further:** Continuing
to lower the threshold to force this specific case to pass would reduce the
system's ability to correctly escalate genuinely low-confidence or
out-of-scope queries elsewhere — trading one failure mode for another
rather than solving the underlying issue.

**How production RAG systems typically address this** (beyond this
assignment's scope): hybrid search (keyword/BM25 + vector), query rewriting
before embedding, domain-benchmarked embedding models, or reranking
retrieved candidates with a secondary model.

**Conclusion:** The 0.30 threshold was empirically tuned from observed score
distributions on `gemini-embedding-001`. The system fails safe (escalates to
a human) rather than fails open (confidently hallucinates) in these edge
cases — the correct tradeoff for customer support.

### 3. Genuine knowledge base gaps

Some queries (e.g., "how do I generate a new API key") were initially
unanswerable because the topic wasn't covered in the source documents. The
system correctly identified this as low-confidence and escalated rather
than hallucinating an answer. This specific gap was subsequently fixed by
adding the missing content to `api_troubleshooting.md` and re-ingesting,
demonstrating that the escalation behavior is a genuine safety net, not
just a tuning artifact.

### 4. Transient API errors

The Gemini API occasionally returns `503 UNAVAILABLE` errors during high
demand. This is mitigated with an exponential backoff retry wrapper
(`src/retry_utils.py`) that retries transient errors up to 4 times before
failing.

## Test Scenarios

| Message | Expected Persona | Result |
|---|---|---|
| "It's been an hour and nothing is loading!" | Frustrated User | Pass — empathetic tone, simple steps |
| "What are the header parameters for bearer token auth?" | Technical Expert | Escalates (see Limitation 2) |
| "We need a timeline for billing dispute resolution." | Business Executive | Pass — brief, timeline-focused |
| "Database integration causing internal errors." | Technical Expert | Pass — step-by-step from docs |
| "Duplicate charges, demand immediate refund!" | Frustrated User | Pass — escalates with handoff JSON |