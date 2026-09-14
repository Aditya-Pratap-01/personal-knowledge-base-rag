import os
import html
import time

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
# CUSTOM UI / CSS
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
        padding: 0 !important;
    }

    .block-container {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }


    /* =====================================================
       HIDE STREAMLIT DEFAULT UI
    ===================================================== */

    header {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }

    footer,
    [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;

        height: 0 !important;
        min-height: 0 !important;

        padding: 0 !important;
        margin: 0 !important;

        border: none !important;
    }


    /* =====================================================
       STREAMLIT BOTTOM AREA
    ===================================================== */

    [data-testid="stBottom"] {
        background: #f4f6fb !important;
        border: none !important;
        box-shadow: none !important;
    }

    [data-testid="stBottomBlockContainer"] {
        background: #f4f6fb !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }


    /* =====================================================
       CHAT SCROLL AREA
    ===================================================== */

    .chat-scroll {
        height: 455px;

        overflow-y: auto;
        overflow-x: hidden;

        display: flex;

        flex-direction: column-reverse;

        padding:
            10px
            7px
            12px
            7px;

        box-sizing: border-box;

        overscroll-behavior: contain;
    }

    .chat-scroll::-webkit-scrollbar {
        width: 6px;
    }

    .chat-scroll::-webkit-scrollbar-track {
        background: transparent;
    }

    .chat-scroll::-webkit-scrollbar-thumb {
        background: #c5ccda;
        border-radius: 10px;
    }


    /* =====================================================
       WELCOME MESSAGE
    ===================================================== */

    .welcome-card {
        width: 100%;

        display: flex;

        align-items: flex-end;

        gap: 9px;

        margin-bottom: 14px;
    }

    .welcome-bubble {
        max-width: 78%;

        padding:
            13px
            15px;

        border-radius: 17px;

        border-top-left-radius: 7px;

        background: #ffffff;

        color: #1c2942;

        border:
            1px solid
            #dde3ee;

        font-size: 14px;

        line-height: 1.58;

        box-shadow:
            0 3px 10px
            rgba(20, 35, 60, 0.05);
    }


    /* =====================================================
       MESSAGE ROW
    ===================================================== */

    .message-row {
        width: 100%;

        display: flex;

        align-items: flex-end;

        gap: 9px;

        margin-bottom: 14px;
    }

    .message-row.assistant {
        justify-content: flex-start;
    }

    .message-row.user {
        justify-content: flex-end;
    }


    /* =====================================================
       AVATARS
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

        border:
            1px solid
            #f1dce5;
    }

    .user-avatar {
        background: #ffffff;

        border:
            1px solid
            #d9dfeb;

        font-size: 17px;
    }


    /* =====================================================
       MESSAGE BUBBLES
    ===================================================== */

    .message-bubble {
        max-width: 78%;

        padding:
            13px
            15px;

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
       TYPING INDICATOR
    ===================================================== */

    .typing-row {
        width: 100%;

        display: flex;

        align-items: flex-end;

        gap: 9px;

        margin-bottom: 14px;
    }

    .typing-avatar {
        width: 36px;
        height: 36px;

        min-width: 36px;

        border-radius: 11px;

        display: flex;

        align-items: center;
        justify-content: center;

        background: #fff3f7;

        border:
            1px solid
            #f1dce5;

        font-size: 19px;
    }

    .typing-bubble {
        background: #ffffff;

        border:
            1px solid
            #dde3ee;

        border-radius: 17px;

        border-top-left-radius: 7px;

        padding:
            13px
            17px;

        min-width: 70px;

        box-shadow:
            0 3px 10px
            rgba(20, 35, 60, 0.05);
    }

    .typing-dots {
        display: flex;

        align-items: center;
        justify-content: center;

        gap: 5px;
    }

    .typing-dot {
        width: 7px;
        height: 7px;

        border-radius: 50%;

        background: #c9ced8;

        animation:
            typingBounce
            1.2s
            infinite
            ease-in-out;
    }

    .typing-dot:nth-child(2) {
        animation-delay: 0.15s;
    }

    .typing-dot:nth-child(3) {
        animation-delay: 0.30s;
    }

    @keyframes typingBounce {

        0%,
        60%,
        100% {
            transform: translateY(0);
            opacity: 0.45;
        }

        30% {
            transform: translateY(-4px);
            opacity: 1;
        }
    }


    /* =====================================================
       INPUT FORM
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

        margin-top:
            0 !important;

        box-shadow:
            0 4px 15px
            rgba(20, 35, 60, 0.06) !important;
    }

    div[data-testid="stForm"] > div {
        background:
            transparent !important;
    }


    /* =====================================================
       INPUT + SEND BUTTON SAME LINE
    ===================================================== */

    div[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        display: flex !important;

        flex-direction: row !important;

        flex-wrap: nowrap !important;

        align-items: center !important;

        gap: 8px !important;

        width: 100% !important;
    }

    div[data-testid="stForm"] [data-testid="column"] {
        min-width: 0 !important;
    }

    div[data-testid="stForm"] [data-testid="column"]:first-child {
        flex: 1 1 auto !important;

        width: auto !important;

        min-width: 0 !important;
    }

    div[data-testid="stForm"] [data-testid="column"]:last-child {
        flex: 0 0 52px !important;

        width: 52px !important;

        min-width: 52px !important;
    }


    /* =====================================================
       TEXT INPUT
    ===================================================== */

    div[data-testid="stTextInput"] {
        margin-bottom: 0 !important;

        width: 100% !important;
    }

    div[data-testid="stTextInput"] label {
        display: none !important;
    }

    div[data-testid="stTextInput"] > div {
        background:
            #ffffff !important;

        border: none !important;

        box-shadow: none !important;

        width: 100% !important;
    }

    div[data-testid="stTextInput"] input {
        background:
            #ffffff !important;

        border:
            1px solid
            #cbd4e2 !important;

        border-radius:
            13px !important;

        color:
            #1b2740 !important;

        font-size:
            14px !important;

        padding:
            12px
            14px !important;

        min-height:
            44px !important;

        width: 100% !important;

        box-shadow:
            none !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color:
            #315d91 !important;

        box-shadow:
            0 0 0 2px
            rgba(49, 93, 145, 0.10) !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color:
            #8a93a5 !important;
    }

    [data-testid="InputInstructions"] {
        display: none !important;
    }


    /* =====================================================
       SMALL SEND BUTTON
    ===================================================== */

    div[data-testid="stFormSubmitButton"] {
        width: 52px !important;

        min-width: 52px !important;

        margin: 0 !important;
    }

    div[data-testid="stFormSubmitButton"] button {
        width: 52px !important;

        min-width: 52px !important;

        height: 44px !important;

        padding: 0 !important;

        border: none !important;

        border-radius:
            13px !important;

        background:
            linear-gradient(
                135deg,
                #173b67,
                #244e85
            ) !important;

        color:
            #ffffff !important;

        font-size:
            18px !important;

        font-weight:
            600 !important;

        box-shadow:
            none !important;
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
       DISCLAIMER
    ===================================================== */

    .custom-disclaimer {
        text-align:
            center;

        color:
            #8a93a5;

        font-size:
            10px;

        line-height:
            1.4;

        padding:
            7px
            8px
            4px
            8px;

        margin:
            0;
    }


    /* =====================================================
       MOBILE
    ===================================================== */

    @media (max-width: 600px) {

        .chat-scroll {
            height:
                430px;

            flex-direction:
                column-reverse;
        }

        .message-bubble,
        .welcome-bubble {
            max-width:
                82%;
        }

        .avatar,
        .typing-avatar {
            width:
                33px;

            height:
                33px;

            min-width:
                33px;
        }

        .custom-disclaimer {
            font-size:
                9px;
        }

        /*
           Keep input and send button together
           even on mobile.
        */

        div[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }

        div[data-testid="stForm"] [data-testid="column"]:last-child {
            flex: 0 0 52px !important;

            width: 52px !important;

            min-width: 52px !important;
        }

        div[data-testid="stFormSubmitButton"] button {
            width: 52px !important;

            min-width: 52px !important;
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
# HELPER FUNCTIONS
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

        return f"""
        <div class="message-row user">

            <div class="message-bubble user-bubble">
                {safe_content}
            </div>

            <div class="avatar user-avatar">
                👤
            </div>

        </div>
        """

    return f"""
    <div class="message-row assistant">

        <div class="avatar assistant-avatar">
            🧠
        </div>

        <div class="message-bubble assistant-bubble">
            {safe_content}
        </div>

    </div>
    """


def render_typing():

    return """
    <div class="typing-row">

        <div class="typing-avatar">
            🧠
        </div>

        <div class="typing-bubble">

            <div class="typing-dots">

                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>

            </div>

        </div>

    </div>
    """


def render_welcome():

    return """
    <div class="welcome-card">

        <div class="avatar assistant-avatar">
            🧠
        </div>

        <div class="welcome-bubble">

            <strong>
                Hi! 👋
            </strong>

            <br><br>

            Ask me anything about your uploaded
            knowledge base.

        </div>

    </div>
    """


# =========================================================
# BUILD CHAT HTML
#
# IMPORTANT:
# With column-reverse:
# newest content must come FIRST in the DOM.
# =========================================================

def build_chat_html(
    messages,
    show_typing=False,
):

    parts = []


    # -----------------------------------------------------
    # TYPING IS THE NEWEST ELEMENT
    # -----------------------------------------------------

    if show_typing:

        parts.append(
            render_typing()
        )


    # -----------------------------------------------------
    # ADD MESSAGES FROM NEWEST TO OLDEST
    # -----------------------------------------------------

    for message in reversed(messages):

        parts.append(
            render_message(
                message["role"],
                message["content"],
            )
        )


    # -----------------------------------------------------
    # WELCOME GOES AT VISUAL TOP
    # -----------------------------------------------------

    parts.append(
        render_welcome()
    )


    return "\n".join(parts)


# =========================================================
# CHAT PLACEHOLDER
# =========================================================

chat_placeholder = st.empty()


# =========================================================
# INITIAL CHAT
# =========================================================

chat_placeholder.html(
    f"""
    <div class="chat-scroll">

        {build_chat_html(
            st.session_state.messages,
            show_typing=False,
        )}

    </div>
    """
)


# =========================================================
# INPUT FORM
# =========================================================

with st.form(
    "knowledge_chat_form",
    clear_on_submit=True,
):

    col1, col2 = st.columns(
        [0.88, 0.12],
        vertical_alignment="center",
    )


    with col1:

        question = st.text_input(
            "Question",
            placeholder="Ask something...",
            label_visibility="collapsed",
        )


    with col2:

        submitted = st.form_submit_button(
            "➤",
            use_container_width=True,
        )


# =========================================================
# DISCLAIMER
# =========================================================

st.html(
    """
    <div class="custom-disclaimer">
        This chatbot uses AI to generate responses and may
        occasionally make mistakes.
    </div>
    """
)


# =========================================================
# PROCESS QUESTION
# =========================================================

if submitted and question.strip():

    question = question.strip()


    # =====================================================
    # USER MESSAGE APPEARS IMMEDIATELY
    # =====================================================

    updated_messages = (
        st.session_state.messages
        + [
            {
                "role": "user",
                "content": question,
            }
        ]
    )


    # =====================================================
    # SHOW USER + TYPING INDICATOR
    # =====================================================

    chat_placeholder.html(
        f"""
        <div class="chat-scroll">

            {build_chat_html(
                updated_messages,
                show_typing=True,
            )}

        </div>
        """
    )


    # =====================================================
    # WAIT 2 SECONDS
    # =====================================================

    time.sleep(2)


    # =====================================================
    # DETERMINE ANSWER
    # =====================================================

    if is_greeting(question):

        answer = (
            "Hi! 👋\n"
            "Ask me anything about your "
            "uploaded knowledge base."
        )


    elif is_thanks(question):

        answer = (
            "You're welcome! 😊\n"
            "Feel free to ask me anything "
            "about your knowledge base."
        )


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

            context = "\n".join(
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

                answer = answer.replace(
                    "**",
                    ""
                )

            except Exception:

                answer = (
                    "Sorry, I couldn't process "
                    "that question right now."
                )


    # =====================================================
    # WORD-BY-WORD RESPONSE
    # =====================================================

    words = answer.split()

    streamed_answer = ""


    for index, word in enumerate(words):

        if index == 0:

            streamed_answer = word

        else:

            streamed_answer += " " + word


        animated_messages = (
            updated_messages
            + [
                {
                    "role": "assistant",
                    "content": streamed_answer,
                }
            ]
        )


        chat_placeholder.html(
            f"""
            <div class="chat-scroll">

                {build_chat_html(
                    animated_messages,
                    show_typing=False,
                )}

            </div>
            """
        )


        time.sleep(0.03)


    # =====================================================
    # SAVE FINAL ANSWER
    # =====================================================

    st.session_state.messages = (
        updated_messages
        + [
            {
                "role": "assistant",
                "content": answer,
            }
        ]
    )


    # =====================================================
    # FINAL RENDER
    # =====================================================

    chat_placeholder.html(
        f"""
        <div class="chat-scroll">

            {build_chat_html(
                st.session_state.messages,
                show_typing=False,
            )}

        </div>
        """
    )