import os

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

st.set_page_config(
    page_title="Personal Knowledge Base",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Personal Knowledge Base Assistant")
st.caption(
    "Ask questions only about your uploaded notes. "
    "Answers include the exact source chunks."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("1. Add notes")

    uploaded_files = st.file_uploader(
        "Upload .txt, .md or .pdf files",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files and st.button(
        "Index uploaded notes",
        type="primary",
    ):
        with st.spinner(
            "Reading, chunking and embedding your notes..."
        ):
            result = ingest_documents(uploaded_files)

        st.success(
            f"Indexed {result['files']} file(s), "
            f"{result['chunks']} chunk(s)."
        )

    st.divider()

    st.metric(
        "Stored chunks",
        get_collection_count(),
    )


# ---------------------------------------------------------
# Clear Knowledge Base
# ---------------------------------------------------------

if st.button("🗑️ Clear Knowledge Base"):
    clear_collection()

    st.success("Knowledge base cleared.")

    st.rerun()


st.info(
    "The app retrieves relevant chunks first and uses "
    "conversation history to understand follow-up questions. "
    "The LLM is instructed to answer only from your notes."
)


# ---------------------------------------------------------
# Groq API
# ---------------------------------------------------------

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.warning(
        "GROQ_API_KEY is not set. Create a .env file in this "
        "project and add:\n\n"
        "GROQ_API_KEY=your_key_here"
    )

    st.stop()

client = Groq(api_key=api_key)


# ---------------------------------------------------------
# Conversation Memory
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------------------------------------------------------
# Intent Detection
# ---------------------------------------------------------

def is_greeting(text):
    text = text.lower().strip()

    greetings = [
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "helo",
        "namaste",
        "good morning",
        "good afternoon",
        "good evening",
    ]

    return text in greetings


def is_thanks(text):
    text = text.lower().strip()

    thanks_words = [
        "thanks",
        "thank you",
        "thx",
        "ty",
        "thanks bhai",
        "thank you bhai",
    ]

    return text in thanks_words


def is_memory_question(text):
    text = text.lower().strip()

    memory_questions = [
        "what was my last question",
        "what was my previous question",
        "what did i ask last",
        "what did i ask before",
        "what did i just ask",
        "what was the question i asked",
        "what was my last query",
        "what did i ask previously",
        "what was my previous query",
    ]

    return any(
        phrase in text
        for phrase in memory_questions
    )


# ---------------------------------------------------------
# Display Conversation History
# ---------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------------------------------------------------
# User Question
# ---------------------------------------------------------

question = st.chat_input(
    "Ask something about your notes..."
)


if question:

    # -----------------------------------------------------
    # Save current user message
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)


    # -----------------------------------------------------
    # Greeting
    # -----------------------------------------------------

    if is_greeting(question):

        answer = (
            "Hello! 👋 How can I help you? "
            "You can ask questions about your uploaded notes."
        )

        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.stop()


    # -----------------------------------------------------
    # Thanks
    # -----------------------------------------------------

    if is_thanks(question):

        answer = "You're welcome bhai! 😊"

        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.stop()


    # -----------------------------------------------------
    # Conversation Memory Question
    # -----------------------------------------------------

    if is_memory_question(question):

        # Exclude the current question.
        previous_user_questions = [
            message["content"]
            for message in st.session_state.messages[:-1]
            if message["role"] == "user"
        ]

        if previous_user_questions:

            last_question = previous_user_questions[-1]

            answer = (
                f'Your last question was: "{last_question}"'
            )

        else:

            answer = (
                "You haven't asked me a previous question "
                "in this conversation yet."
            )

        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.stop()


    # -----------------------------------------------------
    # Assistant / RAG
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        # -------------------------------------------------
        # Build conversation context
        # -------------------------------------------------

        recent_messages = st.session_state.messages[-7:]

        conversation_history = []

        for message in recent_messages:

            role = message["role"].upper()

            conversation_history.append(
                f"{role}: {message['content']}"
            )

        conversation_history = "\n".join(
            conversation_history
        )


        # -------------------------------------------------
        # Retrieval
        # -------------------------------------------------

        retrieval_query = f"""
Previous conversation:

{conversation_history}

Current question:

{question}
"""

        with st.spinner("Searching your notes..."):

            results = search_documents(
                retrieval_query,
                top_k=5,
            )


        # -------------------------------------------------
        # No relevant information
        # -------------------------------------------------

        if not results:

            answer = (
                "I couldn't find relevant information in "
                "your uploaded notes, so I won't guess."
            )

            st.markdown(answer)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            st.stop()


        # -------------------------------------------------
        # Build retrieved context
        # -------------------------------------------------

        context_parts = []

        for i, item in enumerate(
            results,
            start=1,
        ):

            context_parts.append(
                f"[SOURCE {i}]\n"
                f"File: {item['source']}\n"
                f"Chunk ID: {item['chunk_id']}\n"
                f"Text:\n{item['text']}"
            )

        context = "\n\n".join(
            context_parts
        )


        # -------------------------------------------------
        # LLM Instructions
        # -------------------------------------------------

        system_prompt = """You are a strict personal
knowledge-base assistant.

RULES:

1. Answer ONLY using the supplied SOURCE text.

2. You may use the conversation history to understand
what the user is referring to.

3. Do not use outside knowledge or assumptions.

4. If the sources do not contain enough information to
answer the question, respond EXACTLY with:

"I couldn't find enough information in your notes to answer that."

5. When you use information from a source, cite the
relevant source like [SOURCE 1].

6. If you cannot answer from the sources, do NOT include
any [SOURCE] citation.

7. Keep the answer clear and concise.
"""


        user_prompt = f"""Conversation history:

{conversation_history}

Current user question:

{question}

Retrieved sources:

{context}
"""


        # -------------------------------------------------
        # Groq
        # -------------------------------------------------

        try:

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0,
            )

            answer = response.choices[0].message.content

        except Exception as e:

            answer = f"Groq API error: {e}"


        # -------------------------------------------------
        # Display Answer
        # -------------------------------------------------

        st.markdown(answer)


        # -------------------------------------------------
        # Show exact chunks only for supported answers
        # -------------------------------------------------

        refusal_text = (
            "I couldn't find enough information "
            "in your notes to answer that."
        )

        if refusal_text not in answer:

            st.subheader("Exact chunks used")

            for i, item in enumerate(
                results,
                start=1,
            ):

                with st.expander(
                    f"[SOURCE {i}] — "
                    f"{item['source']} — "
                    f"chunk {item['chunk_id']}"
                ):

                    st.code(
                        item["text"]
                    )


        # -------------------------------------------------
        # Save assistant answer
        # -------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )