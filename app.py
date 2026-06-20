import sys
import os

# Make sure Python can find our modules inside the src/ folder
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
from classifier import classify_customer_persona
from rag_pipeline import LocalRAGPipeline
from generator import generate_adaptive_response
from config import TOP_K_RESULTS

st.set_page_config(page_title="Persona-Adaptive Support Agent", page_icon="🎧")

st.title("Persona-Adaptive Customer Support Agent")
st.caption(
    "This assistant detects your communication style and tailors its response "
    "accordingly, using only our internal knowledge base."
)


@st.cache_resource
def load_pipeline():
    """
    Loads the RAG pipeline once and reuses it across reruns.
    On a fresh deployment (e.g. Streamlit Cloud), chroma_db/ won't exist yet,
    so we auto-ingest the data/ folder the first time the collection is empty.
    """
    from rag_pipeline import load_data_folder

    pipeline = LocalRAGPipeline()

    if pipeline.collection.count() == 0:
        with st.spinner("First-time setup: indexing knowledge base..."):
            load_data_folder(pipeline, data_dir="data")

    return pipeline


pipeline = load_pipeline()

# Initialize chat history in Streamlit's session state.
# Session state persists across reruns within the same browser tab/session.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Re-display the full chat history on every rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("persona"):
            st.caption(f"Detected persona: {message['persona']}")

# The chat input box at the bottom of the page
user_input = st.chat_input("Type your support question here...")

if user_input:
    # 1. Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Run the full pipeline: classify -> retrieve -> generate
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your message..."):
            persona_result = classify_customer_persona(user_input)
            persona = persona_result["persona"]

            context_chunks = pipeline.retrieve_context(user_input, top_k=TOP_K_RESULTS)

            result = generate_adaptive_response(user_input, persona, context_chunks)

        st.markdown(result["response"])
        st.caption(f"Detected persona: {persona}")

        if result["escalated"]:
            st.warning("This conversation has been escalated to a human agent.")
            with st.expander("View handoff summary (for support staff)"):
                st.code(result["handoff_summary"], language="json")

    # 3. Save assistant's reply into chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["response"],
        "persona": persona
    })

# Sidebar with helpful info for demoing/testing
with st.sidebar:
    st.header("About this Agent")
    st.write(
        "This support agent classifies your message into one of three personas "
        "and adapts its tone accordingly:"
    )
    st.markdown("- **Technical Expert** — detailed, jargon-friendly\n"
                "- **Frustrated User** — empathetic, simple steps\n"
                "- **Business Executive** — brief, outcome-focused")
    st.divider()
    st.write("Knowledge base topics covered:")
    st.markdown("- Password resets\n- API troubleshooting\n- Billing & refunds\n- General account support")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()