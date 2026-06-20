import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
import chromadb
from pypdf import PdfReader

load_dotenv()


class LocalRAGPipeline:
    def __init__(self, db_dir="./chroma_db"):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        # PersistentClient saves the database to disk so we don't have to
        # re-ingest documents every time we run the program.
        self.chroma_client = chromadb.PersistentClient(path=db_dir)
        self.collection = self.chroma_client.get_or_create_collection(name="support_kb")

    def get_embedding(self, text: str) -> list:
        """Calls Gemini's embedding model to turn text into a vector of numbers."""
        response = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )
        return response.embeddings[0].values

    def ingest_document(self, doc_name: str, content: str):
        """Splits a document into chunks and stores each chunk's embedding in ChromaDB."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(content)

        for idx, chunk in enumerate(chunks):
            embedding = self.get_embedding(chunk)
            chunk_id = f"{doc_name}_chunk_{idx}"

            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[{"source": doc_name, "chunk_index": idx}],
                documents=[chunk]
            )
        print(f"Ingested {len(chunks)} chunks from {doc_name}")

    def retrieve_context(self, query: str, top_k: int = 3) -> list:
        """Embeds the query and finds the most similar document chunks in ChromaDB."""
        query_vector = self.get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )

        retrieved_items = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                retrieved_items.append({
                    "text": results['documents'][0][i],
                    "source": results['metadatas'][0][i]['source'],
                    # ChromaDB returns distance (lower = more similar).
                    # We convert it to a similarity-style score (higher = better match).
                    "score": 1.0 - (results['distances'][0][i] if results['distances'] else 0.0)
                })
        return retrieved_items


def load_data_folder(pipeline: LocalRAGPipeline, data_dir: str = "data"):
    """Reads every .txt, .md, and .pdf file in the data folder and ingests it."""
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)

        if filename.endswith(".txt") or filename.endswith(".md"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            pipeline.ingest_document(filename, text)

        elif filename.endswith(".pdf"):
            reader = PdfReader(filepath)
            pdf_text = ""
            for page in reader.pages:
                pdf_text += page.extract_text() + "\n"
            pipeline.ingest_document(filename, pdf_text)


# This only runs when you execute this file directly: python src/rag_pipeline.py
if __name__ == "__main__":
    pipeline = LocalRAGPipeline()

    print("Ingesting documents from /data ...")
    load_data_folder(pipeline, data_dir="data")

    print("\n--- Testing retrieval ---")
    test_queries = [
        "How do I reset my password?",
        "I got a 401 error from the API",
        "Can I get a refund for duplicate charges?"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = pipeline.retrieve_context(query, top_k=2)
        for r in results:
            print(f"  Source: {r['source']} | Score: {r['score']:.3f}")
            print(f"  Text: {r['text'][:150]}...")