import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from rag import (
    ingest_documents,
    search_documents,
    get_collection_count,
    clear_collection,
)

load_dotenv()

st.set_page_config(page_title="Personal Knowledge Base", page_icon="📚", layout="wide")

st.title("📚 Personal Knowledge Base Assistant")
st.caption("Ask questions only about your uploaded notes. Answers include the exact source chunks.")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Add Files")
    uploaded_files = st.file_uploader(
        "Upload .txt, .md or .pdf files",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files and st.button("Index uploaded notes", type="primary"):
        with st.spinner("Reading, chunking and embedding your notes..."):
            result = ingest_documents(uploaded_files)
        st.success(
            f"Indexed {result['files']} file(s), {result['chunks']} chunk(s)."
        )

    st.divider()
    st.metric("Stored chunks", get_collection_count())

if st.button("🗑️ Clear Knowledge Base"):
    clear_collection()
    st.success("Knowledge base cleared.")
    st.rerun()

st.info(
    "Hello, How can I help you? You can ask questions about your uploaded notes. "
)

# ---------------- API key check ----------------
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.warning(
        "GROQ_API_KEY is not set. Create a .env file in this project and add:\n\n"
        "GROQ_API_KEY=your_key_here"
    )
    st.stop()

client = Groq(api_key=api_key)

# ---------------- Chat ----------------
question = st.chat_input("Ask something about your notes...")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching your notes..."):
            results = search_documents(question, top_k=5)

        if not results:
            answer = "I couldn't find relevant information in your uploaded notes, so I won't guess."
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.stop()

        context_parts = []
        for i, item in enumerate(results, start=1):
            context_parts.append(
                f"[SOURCE {i}]\n"
                f"File: {item['source']}\n"
                f"Chunk ID: {item['chunk_id']}\n"
                f"Text:\n{item['text']}"
            )

        context = "\n\n".join(context_parts)

        system_prompt = """You are a strict personal knowledge-base assistant.

RULES:
1. Answer ONLY using the supplied SOURCE text.
2. Do not use outside knowledge.
3. If the sources do not contain enough information, say:
   "I couldn't find enough information in your notes to answer that."
4. Every factual claim must have a citation like [SOURCE 1].
5. Keep the answer clear and concise.
"""

        user_prompt = f"""User question:
{question}

Retrieved sources:
{context}
"""

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"Groq API error: {e}"

        st.markdown(answer)

        st.subheader("Exact chunks used")
        for i, item in enumerate(results, start=1):
            with st.expander(f"[SOURCE {i}] — {item['source']} — chunk {item['chunk_id']}"):
                st.code(item["text"])

        st.session_state.messages.append({"role": "assistant", "content": answer})
