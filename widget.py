import os
import html

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
# CUSTOM UI
# =========================================================

st.html(
    """
    <style>

    /* =====================================================
       GLOBAL PAGE
    ===================================================== */

    html,
    body {
        margin: 0 !important;
        padding: 0 !important;

        background: #f4f6fb !important;
    }

    [data-testid="stAppViewContainer"] {
        background: #f4f6fb !important;
    }

    [data-testid="stMain"] {
        background: #f4f6fb !important;
    }

    [data-testid="stMainBlockContainer"] {
        background: #f4f6fb !important;

        padding-top: 10px !important;
        padding-bottom: 10px !important;

        padding-left: 12px !important;
        padding-right: 12px !important;
    }

    .block-container {
        max-width: 100% !important;

        padding-top: 0 !important;
        padding-bottom: 0 !important;

        padding-left: 0 !important;
        padding-right: 0 !important;
    }


    /* =====================================================
       HIDE STREAMLIT DEFAULT ELEMENTS
    ===================================================== */

    header {
        visibility: hidden !important;
        height: 0 !important;
    }

    #MainMenu {
        visibility: hidden !important;
    }

    footer {
        visibility: hidden !important;
        height: 0 !important;
    }


    /* =====================================================
       WELCOME MESSAGE
    ===================================================== */

    .welcome-card {
        background: #ffffff;

        border: 1px solid #dde3ee;

        border-radius: 18px;

        padding: 18px 18px;

        margin: 4px 4px 16px 4px;

        color: #19233b;

        box-shadow:
            0 4px 14px
            rgba(20, 35, 60, 0.05);
    }

    .welcome-title {
        font-size: 18px;

        font-weight: 700;

        color: #18233d;

        margin-bottom: 9px;
    }

    .welcome-text {
        font-size: 14px;

        color: #5e687b;

        line-height: 1.6;
    }


    /* =====================================================
       CHAT AREA
    ===================================================== */

    .chat-area {
        display: flex;

        flex-direction: column;

        gap: 14px;

        padding: 0 4px 10px 4px;
    }


    /* =====================================================
       MESSAGE ROW
    ===================================================== */

    .message-row {
        width: 100%;

        display: flex;

        align-items: flex-end;

        gap: 9px;
    }

    .message-row.assistant {
        justify-content: flex-start;
    }

    .message-row.user {
        justify-content: flex-end;
    }


    /* =====================================================
       AVATAR
    ===================================================== */

    .avatar {
        width: 36px;
        height: 36px;

        min-width: 36px;

        border-radius: 11px;

        display: flex;

        align-items: center;
        justify-content: center;

        font-size: 19px;
    }

    .assistant-avatar {
        background: #fff3f7;
        color: #173b67;

        border: 1px solid #f1dce5;
    }

    .user-avatar {
        background: #ffffff;

        border: 1px solid #d9dfeb;

        font-size: 17px;
    }


    /* =====================================================
       MESSAGE BUBBLE
    ===================================================== */

    .message-bubble {
        max-width: 78%;

        padding: 13px 15px;

        border-radius: 17px;

        font-size: 14px;

        line-height: 1.58;

        word-break: break-word;

        white-space: normal;
    }

    .assistant-bubble {
        background: #ffffff;

        color: #1c2942;

        border:
            1px solid
            #dde3ee;

        border-top-left-radius: 7px;

        box-shadow:
            0 3px 10px
            rgba(20, 35, 60, 0.05);
    }

    .user-bubble {
        background:
            linear-gradient(
                135deg,
                #173b67,
                #244e85
            );

        color: #ffffff;

        border-top-right-radius: 7px;

        box-shadow:
            0 4px 12px
            rgba(23, 59, 103, 0.16);
    }


    /* =====================================================
       INPUT AREA
    ===================================================== */

    .input-heading {
        font-size: 12px;

        color: #788298;

        margin:
            8px
            4px
            6px
            4px;
    }


    /* =====================================================
       STREAMLIT FORM
    ===================================================== */

    div[data-testid="stForm"] {

        background: #ffffff !important;

        border:
            1px solid
            #d7deea !important;

        border-radius:
            16px !important;

        padding:
            8px !important;

        box-shadow:
            0 4px 15px
            rgba(20, 35, 60, 0.06) !important;
    }

    div[data-testid="stForm"] > div {

        background: transparent !important;
    }


    /* =====================================================
       TEXT INPUT
    ===================================================== */

    div[data-testid="stTextInput"] {

        margin-bottom: 0 !important;
    }

    div[data-testid="stTextInput"] label {

        display: none !important;
    }

    div[data-testid="stTextInput"] > div {

        background: #ffffff !important;

        border: none !important;

        box-shadow: none !important;
    }

    div[data-testid="stTextInput"] input {

        background: #ffffff !important;

        border:
            1px solid
            #cbd4e2 !important;

        border-radius:
            13px !important;

        color: #1b2740 !important;

        font-size: 14px !important;

        padding:
            12px
            14px !important;

        min-height: 44px !important;

        box-shadow: none !important;
    }

    div[data-testid="stTextInput"] input:focus {

        border-color:
            #315d91 !important;

        box-shadow:
            0 0 0 2px
            rgba(49, 93, 145, 0.10) !important;
    }

    div[data-testid="stTextInput"] input::placeholder {

        color: #8a93a5 !important;
    }


    /* =====================================================
       BUTTONS
    ===================================================== */

    div[data-testid="stFormSubmitButton"] button {

        height: 44px !important;

        min-width: 48px !important;

        border: none !important;

        border-radius: 13px !important;

        background:
            linear-gradient(
                135deg,
                #173b67,
                #244e85
            ) !important;

        color: #ffffff !important;

        font-size: 18px !important;

        font-weight: 600 !important;

        box-shadow: none !important;
    }

    div[data-testid="stFormSubmitButton"] button:hover {

        background:
            linear-gradient(
                135deg,
                #244e85,
                #315d91
            ) !important;
    }


    /* =====================================================
       MOBILE
    ===================================================== */

    @media (max-width: 600px) {

        .message-bubble {
            max-width: 82%;
        }

        .avatar {
            width: 33px;
            height: 33px;

            min-width: 33px;
        }

        .welcome-card {
            margin-left: 2px;
            margin-right: 2px;
        }

    }

    </style>
    """
)


# =========================================================
# GROQ
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


if not GROQ_API_KEY:

    try:

        GROQ_API_KEY = st.secrets.get(
            "GROQ_API_KEY"
        )

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
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# =========================================================
# WELCOME
# =========================================================

if "welcome_shown" not in st.session_state:

    st.html(
        """
        <div class="welcome-card">

            <div class="welcome-title">
                Hi! 👋
            </div>

            <div class="welcome-text">
                Ask me anything about your uploaded
                knowledge base.
            </div>

        </div>
        """
    )

    st.session_state.welcome_shown = True


# =========================================================
# MESSAGE RENDERER
# =========================================================

def render_message(
    role,
    content,
):

    safe_content = html.escape(
        content
    ).replace(
        "\n",
        "<br>"
    )

    if role == "user":

        st.html(
            f"""
            <div class="message-row user">

                <div class="message-bubble user-bubble">
                    {safe_content}
                </div>

                <div class="avatar user-avatar">
                    👤
                </div>

            </div>
            """
        )

    else:

        st.html(
            f"""
            <div class="message-row assistant">

                <div class="avatar assistant-avatar">
                    🧠
                </div>

                <div class="message-bubble assistant-bubble">
                    {safe_content}
                </div>

            </div>
            """
        )


# =========================================================
# CHAT HISTORY
# =========================================================

for message in st.session_state.messages:

    render_message(
        message["role"],
        message["content"],
    )


# =========================================================
# GREETING
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


# =========================================================
# THANKS
# =========================================================

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
# INPUT LABEL
# =========================================================

st.html(
    """
    <div class="input-heading">
        Ask something about your notes
    </div>
    """
)


# =========================================================
# CUSTOM INPUT FORM
# =========================================================

with st.form(
    "knowledge_chat_form",
    clear_on_submit=True,
):

    col1, col2, col3 = st.columns(
        [0.08, 0.82, 0.10],
        vertical_alignment="center",
    )


    with col1:

        st.write("🎙️")


    with col2:

        question = st.text_input(
            "Question",
            placeholder="Ask something...",
            label_visibility="collapsed",
        )


    with col3:

        submitted = st.form_submit_button(
            "➤",
            use_container_width=True,
        )


# =========================================================
# PROCESS QUESTION
# =========================================================

if submitted and question.strip():

    question = question.strip()


    # =====================================================
    # SAVE USER MESSAGE
    # =====================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
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
    # RAG SEARCH
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

                response = (
                    client
                    .chat
                    .completions
                    .create(
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
                )


                answer = (
                    response
                    .choices[0]
                    .message
                    .content
                    .strip()
                )


            except Exception:

                answer = (
                    "Sorry, I couldn't process "
                    "that question right now."
                )


    # =====================================================
    # SAVE ASSISTANT MESSAGE
    # =====================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


    # =====================================================
    # RERUN FOR CLEAN DISPLAY
    # =====================================================

    st.rerun()