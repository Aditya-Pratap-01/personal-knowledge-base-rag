import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from rag import (
    ingest_local_notes,
    search_documents,
    get_collection_count,
)

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Personal Knowledge Base",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    #MainMenu {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 700px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# GROQ
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is not configured.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# =========================================================
# AUTO-INDEX NOTES
# =========================================================

if "widget_notes_indexed" not in st.session_state:
    with st.spinner("📚 Preparing knowledge base..."):
        try:
            ingest_local_notes()
            st.session_state.widget_notes_indexed = True
        except Exception as e:
            st.error(f"Knowledge base error: {e}")
            st.stop()

# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div style="text-align:center;">
        <h2>💬 Personal Knowledge Base</h2>
        <p style="color:gray;">
            Ask me about your notes
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# CHAT HISTORY
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask something about your notes..."
)

if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    # -----------------------------------------------------
    # SEARCH KNOWLEDGE BASE
    # -----------------------------------------------------

    results = search_documents(
        question,
        top_k=5,
    )

    if not results:

        answer = (
            "I couldn't find that information "
            "in your uploaded notes."
        )

    else:

        context = "\n\n".join(
            [
                f"Source: {result['source']}\n"
                f"Content:\n{result['text']}"
                for result in results
            ]
        )

        prompt = f"""
You are a helpful Personal Knowledge Base Assistant.

Answer the user's question ONLY using the context below.

If the answer is not present in the context, say:

"I couldn't find that information in your uploaded notes."

Do not make up information.

Keep the answer concise and clear.

Context:
{context}

User question:
{question}
"""

        try:

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Answer questions only from "
                            "the provided knowledge base context."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
            )

            answer = (
                response
                .choices[0]
                .message
                .content
            )

        except Exception as e:

            answer = (
                "Sorry, I couldn't process that question "
                "right now."
            )

    # -----------------------------------------------------
    # SHOW ANSWER
    # -----------------------------------------------------

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )