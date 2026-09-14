import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from rag import (
    ingest_local_notes,
    search_documents,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Knowledge Assistant",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================================================
# LIGHT THEME + CUSTOM CSS
# =========================================================

st.html(
    """
    <style>

    html, body {
        background: #f7f8ff !important;
    }

    [data-testid="stAppViewContainer"] {
        background: #f7f8ff !important;
    }

    [data-testid="stMain"] {
        background: #f7f8ff !important;
    }

    [data-testid="stMainBlockContainer"] {
        background: #f7f8ff !important;
    }

    [data-testid="stBottom"] {
        background: #ffffff !important;
    }

    header {
        visibility: hidden !important;
    }

    #MainMenu {
        visibility: hidden !important;
    }

    footer {
        visibility: hidden !important;
    }

    .block-container {
        max-width: 700px !important;

        padding-top: 0.4rem !important;
        padding-bottom: 0.4rem !important;

        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }


    /* =====================================================
       HEADER
    ===================================================== */

    .assistant-header {
        width: 100%;

        padding: 16px 18px;

        border-radius: 16px 16px 0 0;

        background:
            linear-gradient(
                135deg,
                #173b67,
                #244e85
            );

        color: white;

        box-shadow:
            0 4px 18px
            rgba(23, 59, 103, 0.16);
    }

    .assistant-row {
        display: flex;

        align-items: center;

        gap: 10px;
    }

    .assistant-icon {
        width: 38px;
        height: 38px;

        border-radius: 50%;

        background: #fff3f8;

        display: flex;

        align-items: center;
        justify-content: center;

        font-size: 21px;
    }

    .assistant-title {
        font-size: 20px;
        font-weight: 700;
    }

    .assistant-status {
        margin-top: 5px;
        margin-left: 48px;

        font-size: 13px;
        font-weight: 600;

        color: #d6f8df;
    }

    .online-dot {
        display: inline-block;

        width: 8px;
        height: 8px;

        border-radius: 50%;

        background: #4ade80;

        margin-right: 5px;
    }


    /* =====================================================
       WELCOME
    ===================================================== */

    .welcome-card {
        margin: 14px 6px 10px;

        padding: 15px;

        background: white;

        border:
            1px solid
            #e2e7f0;

        border-radius: 15px;

        color: #18233d;

        font-size: 14px;

        line-height: 1.55;

        box-shadow:
            0 2px 10px
            rgba(15, 23, 42, 0.05);
    }


    /* =====================================================
       STREAMLIT CHAT MESSAGES
    ===================================================== */

    [data-testid="stChatMessage"] {
        background: transparent !important;

        padding:
            4px
            4px
            8px
            4px;
    }

    [data-testid="stChatMessageContent"] {
        border-radius: 15px !important;

        padding:
            11px
            14px !important;

        background:
            #eef1f7 !important;

        border:
            1px solid
            #dfe4ed !important;

        color:
            #18233d !important;

        font-size:
            14px !important;

        line-height:
            1.55 !important;
    }


    /* USER MESSAGE */

    [data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-user"]
    )
    [data-testid="stChatMessageContent"] {

        background:
            linear-gradient(
                135deg,
                #173b67,
                #244e85
            ) !important;

        border: none !important;

        color: white !important;
    }

    [data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-user"]
    )
    [data-testid="stChatMessageContent"] p {

        color: white !important;
    }


    /* =====================================================
       CHAT INPUT
    ===================================================== */

    [data-testid="stChatInput"] {
        background: white !important;

        padding-top: 8px !important;

        border-top:
            1px solid
            #e1e5ec !important;
    }

    [data-testid="stChatInput"] > div {
        background: white !important;

        border:
            1px solid
            #cbd4e2 !important;

        border-radius:
            13px !important;

        box-shadow:
            0 4px 14px
            rgba(15, 23, 42, 0.06) !important;
    }

    [data-testid="stChatInput"] textarea {
        background: white !important;

        color: #18233d !important;

        font-size: 14px !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #7b8497 !important;
    }


    /* =====================================================
       MOBILE
    ===================================================== */

    @media (max-width: 600px) {

        .assistant-title {
            font-size: 18px;
        }

        .assistant-status {
            margin-left: 47px;
        }

    }

    </style>
    """
)


# =========================================================
# GROQ
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    try:
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
    except Exception:
        GROQ_API_KEY = None

if not GROQ_API_KEY:
    st.error(
        "GROQ_API_KEY is not configured."
    )
    st.stop()

client = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# AUTO-INDEX NOTES
# =========================================================

if "widget_notes_indexed" not in st.session_state:

    with st.spinner(
        "Preparing knowledge base..."
    ):

        try:
            ingest_local_notes()

            st.session_state.widget_notes_indexed = True

        except Exception as e:

            st.error(
                f"Knowledge base error: {e}"
            )

            st.stop()


# =========================================================
# HEADER
# =========================================================

st.html(
    """
    <div class="assistant-header">

        <div class="assistant-row">

            <div class="assistant-icon">
                🧠
            </div>

            <div class="assistant-title">
                Knowledge Assistant
            </div>

        </div>

        <div class="assistant-status">

            <span class="online-dot"></span>

            Online

        </div>

    </div>
    """
)


# =========================================================
# WELCOME
# =========================================================

if "welcome_shown" not in st.session_state:

    st.html(
        """
        <div class="welcome-card">

            <strong>
                Hi! 👋
            </strong>

            <br><br>

            Ask me anything about your uploaded
            knowledge base.

        </div>
        """
    )

    st.session_state.welcome_shown = True


# =========================================================
# CHAT HISTORY
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# HELPERS
# =========================================================

def is_greeting(text):

    greetings = {
        "hi",
        "hii",
        "hiii",
        "hello",
        "hey",
        "hey bhai",
        "namaste",
        "good morning",
        "good afternoon",
        "good evening",
    }

    return (
        text.lower().strip()
        in greetings
    )


def is_thanks(text):

    thanks_words = {
        "thanks",
        "thank you",
        "thankyou",
        "thx",
        "ty",
        "thanks bhai",
        "thank you bhai",
    }

    return (
        text.lower().strip()
        in thanks_words
    )


# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask something..."
)


if question:

    question = question.strip()


    # -----------------------------------------------------
    # STORE USER MESSAGE
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )


    # -----------------------------------------------------
    # DISPLAY USER MESSAGE
    # -----------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            question
        )


    # =====================================================
    # GREETING
    # =====================================================

    if is_greeting(question):

        answer = (
            "Hi! 👋\n\n"
            "Ask me anything about your "
            "uploaded knowledge base."
        )


    # =====================================================
    # THANKS
    # =====================================================

    elif is_thanks(question):

        answer = (
            "You're welcome! 😊\n\n"
            "Feel free to ask me anything "
            "about your knowledge base."
        )


    # =====================================================
    # RAG
    # =====================================================

    else:

        results = search_documents(
            question,
            top_k=5,
        )


        if not results:

            answer = (
                "I couldn't find any relevant "
                "information in your uploaded notes."
            )


        else:

            context = "\n\n".join(
                [
                    (
                        f"Source: {result['source']}\n"
                        f"Content:\n{result['text']}"
                    )
                    for result in results
                ]
            )


            prompt = f"""
You are a helpful Personal Knowledge Base Assistant.

Answer the user's question ONLY using the context below.

If the answer is not present in the context, say:

"I couldn't find any relevant information in your uploaded notes."

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
                                "Answer questions only "
                                "from the provided "
                                "knowledge base context."
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
                    .strip()
                )


            except Exception as e:

                answer = (
                    "Sorry, I couldn't process "
                    "that question right now."
                )


    # =====================================================
    # DISPLAY ASSISTANT
    # =====================================================

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            answer
        )


    # =====================================================
    # STORE ASSISTANT
    # =====================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )