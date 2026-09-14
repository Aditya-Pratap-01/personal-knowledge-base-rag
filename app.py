import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import uuid

from rag import (
    ingest_documents,
    ingest_local_notes,
    search_documents,
    get_collection_count,
    clear_collection,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Personal Knowledge Base",
    page_icon="🧠",
    layout="wide",
)


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error(
        "GROQ_API_KEY nahi mila. Please .env file me API key add karo."
    )
    st.stop()


client = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# CONSTANTS
# =========================================================

REFUSAL_PHRASE = (
    "I couldn't find relevant information in your "
    "uploaded notes, so I won't guess."
)


# =========================================================
# CHAT FUNCTIONS
# =========================================================

def create_chat():
    """Create a new empty chat."""

    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": [],
    }

    st.session_state.current_chat_id = chat_id


def get_current_chat():
    """Get the currently selected chat."""

    return st.session_state.chats[
        st.session_state.current_chat_id
    ]


# =========================================================
# GREETING DETECTION
# =========================================================

def is_greeting(text):

    greetings = [
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "namaste",
        "good morning",
        "good afternoon",
        "good evening",
    ]

    normalized = text.lower().strip()

    return normalized in greetings


# =========================================================
# THANKS DETECTION
# =========================================================

def is_thanks(text):

    thanks_words = [
        "thanks",
        "thank you",
        "thankyou",
        "thx",
        "ty",
        "thanks bhai",
        "thank you bhai",
    ]

    normalized = text.lower().strip()

    return normalized in thanks_words


# =========================================================
# MEMORY QUESTION DETECTION
# =========================================================

def is_memory_question(text):

    normalized = text.lower().strip()

    memory_keywords = [
        # English
        "last question",
        "previous question",
        "my last question",
        "my previous question",
        "what did i ask before",
        "what did i ask earlier",
        "what did i say before",
        "what did i say earlier",
        "what was i asking",
        "what were we talking about",
        "what are we talking about",
        "what did we discuss",

        # Hinglish
        "pichla question",
        "pichla sawaal",
        "last sawaal",
        "previous sawaal",
        "mera pichla question",
        "mera pichla sawaal",
        "mera last question",
        "mera last sawaal",
        "mera previous question",
        "maine pehle kya poocha",
        "maine pehle kya pucha",
        "maine pehle kya poocha tha",
        "maine pehle kya pucha tha",
        "maine pichle baar kya poocha",
        "maine pichle baar kya pucha",
        "maine pichle baar kya poocha tha",
        "maine pichle baar kya pucha tha",
        "maine kya poocha",
        "maine kya pucha",
        "maine kya poocha tha",
        "maine kya pucha tha",
        "maine abhi kya poocha",
        "maine abhi kya pucha",
        "maine abhi kya poocha tha",
        "maine abhi kya pucha tha",
        "hum kya baat kar rahe",
        "hum kis bare mein baat kar rahe",
        "hum kis bare me baat kar rahe",
        "kya discuss kar rahe",
        "abhi hum kya discuss kar rahe",
    ]

    return any(
        keyword in normalized
        for keyword in memory_keywords
    )


# =========================================================
# RECENT CONVERSATION
# =========================================================

def get_recent_conversation(messages, limit=6):

    recent = messages[-limit:]

    conversation = []

    for message in recent:

        role = message.get("role", "")
        content = message.get("content", "")

        if role == "user":

            conversation.append(
                f"User: {content}"
            )

        elif role == "assistant":

            conversation.append(
                f"Assistant: {content}"
            )

    return "\n".join(conversation)


# =========================================================
# MEMORY ANSWER
# =========================================================

def answer_memory_question(messages):

    user_messages = [
        message["content"]
        for message in messages
        if message["role"] == "user"
    ]

    if len(user_messages) <= 1:

        return (
            "Abhi is chat me tumne koi previous question "
            "nahi poocha hai bhai."
        )

    previous_question = user_messages[-2]

    return (
        f"Tumhara previous question tha:\n\n"
        f"> {previous_question}"
    )


# =========================================================
# QUERY CORRECTION
# =========================================================

def correct_query(question, recent_conversation=""):
    """
    Correct only obvious spelling and typing mistakes.

    This function does NOT answer the question.
    """

    correction_prompt = f"""
You are a search-query correction assistant.

Your ONLY job is to correct obvious small spelling,
typing, and transliteration mistakes in the user's query.

Examples:

"dal makhni kaise bnate hai?"
-> "dal makhani kaise banate hai?"

"compny me kitne employes hai?"
-> "company me kitne employees hai?"

"rag systm me grounding kya hai?"
-> "RAG system me grounding kya hai?"

Rules:

1. Preserve the user's original meaning.
2. Do not add new information.
3. Do not answer the question.
4. Do not translate the question.
5. Preserve Hinglish / Roman Hindi if the user used Hinglish.
6. Only fix obvious mistakes.
7. If the query is already fine, return it unchanged.
8. Return ONLY the corrected query.
9. No quotes.
10. No explanation.

Recent conversation:

{recent_conversation}

User query:

{question}
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "system",
                    "content": (
                        "Correct only obvious spelling and "
                        "typing mistakes. Never answer the question."
                    ),
                },
                {
                    "role": "user",
                    "content": correction_prompt,
                },
            ],

            temperature=0,
            max_tokens=100,
        )

        corrected = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        if not corrected:
            return question

        # Safety check.
        if len(corrected) > max(
            len(question) * 2,
            100,
        ):
            return question

        return corrected

    except Exception:

        # If correction fails, use original query.
        return question

# =========================================================
# AUTO-INDEX LOCAL NOTES
# =========================================================

if "local_notes_indexed" not in st.session_state:
    with st.spinner("📚 Knowledge base prepare ho raha hai..."):
        try:
            result = ingest_local_notes()
            st.session_state.local_notes_indexed = True
        except Exception as e:
            st.error(f"Notes indexing failed:\n{e}")
            st.stop()
            
# =========================================================
# SESSION STATE
# =========================================================

if "chats" not in st.session_state:

    st.session_state.chats = {}


if "current_chat_id" not in st.session_state:

    create_chat()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    # -----------------------------------------------------
    # STORED CHUNKS
    # -----------------------------------------------------

    try:

        count = get_collection_count()

        st.metric(
            "Stored Chunks",
            count,
        )

    except Exception:

        st.metric(
            "Stored Chunks",
            0,
        )


    # -----------------------------------------------------
    # CLEAR KNOWLEDGE BASE
    # -----------------------------------------------------

    if st.button(
        "🗑️ Clear Knowledge Base",
        use_container_width=True,
    ):

        try:

            clear_collection()

            st.success(
                "Knowledge Base clear ho gaya."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Knowledge Base clear nahi ho paya:\n{e}"
            )


    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    st.divider()

    st.subheader("💬 History")


    # -----------------------------------------------------
    # NEW CHAT
    # -----------------------------------------------------

    if st.button(
        "🆕 New Chat",
        use_container_width=True,
    ):

        create_chat()

        st.rerun()


    # -----------------------------------------------------
    # CLEAR HISTORY
    # -----------------------------------------------------

    if st.button(
        "🧹 Clear History",
        use_container_width=True,
    ):

        st.session_state.chats = {}

        create_chat()

        st.rerun()


    # -----------------------------------------------------
    # CHAT HISTORY LIST
    # -----------------------------------------------------

    chat_items = list(
        st.session_state.chats.items()
    )

    chat_items.reverse()


    for chat_id, chat in chat_items:

        title = chat["title"]


        # -------------------------------------------------
        # SELECT CHAT
        # -------------------------------------------------

        if st.button(
            title,
            key=f"chat_{chat_id}",
            use_container_width=True,
        ):

            st.session_state.current_chat_id = chat_id

            st.rerun()


        # -------------------------------------------------
        # DELETE SELECTED CHAT
        # -------------------------------------------------

        if (
            st.session_state.current_chat_id
            == chat_id
        ):

            if st.button(
                "🗑️ Delete this chat",
                key=f"delete_{chat_id}",
                use_container_width=True,
            ):

                del st.session_state.chats[
                    chat_id
                ]


                # If no chats remain, create fresh chat.
                if not st.session_state.chats:

                    create_chat()

                else:

                    # Select latest remaining chat.
                    st.session_state.current_chat_id = (
                        next(
                            iter(
                                st.session_state.chats
                            )
                        )
                    )

                st.rerun()


# =========================================================
# CURRENT CHAT
# =========================================================

current_chat = get_current_chat()

messages = current_chat["messages"]


# =========================================================
# MAIN HEADER
# =========================================================

st.title(
    "🧠 Personal Knowledge Base Assistant"
)

st.caption(
    "Ask questions about your uploaded notes. "
    "The assistant will answer only from your knowledge base."
)


# =========================================================
# DISPLAY CHAT MESSAGES
# =========================================================

for message in messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# CHAT INPUT + FILE UPLOAD
# =========================================================

prompt = st.chat_input(
    "Ask something about your notes...",
    accept_file=True,
    file_type=[
        "txt",
        "md",
        "pdf",
    ],
)


# =========================================================
# USER INPUT
# =========================================================

if prompt:

    # -----------------------------------------------------
    # GET QUESTION
    # -----------------------------------------------------

    question = prompt.text.strip()

    uploaded_files = prompt.files


    # =====================================================
    # FILE UPLOAD
    # =====================================================

    if uploaded_files:

        with st.spinner(
            "Documents index ho rahe hain..."
        ):

            try:

                result = ingest_documents(
                    uploaded_files
                )

                st.toast(
                    f"📚 {result['files']} file(s) indexed!",
                    icon="✅",
                )

            except Exception as e:

                st.error(
                    f"Document processing failed:\n{e}"
                )

                st.stop()


        # -------------------------------------------------
        # ONLY FILE UPLOADED
        # -------------------------------------------------

        if not question:

            answer = (
                f"✅ Done bhai!\n\n"
                f"{result['files']} file(s) successfully "
                f"Knowledge Base me add ho gayi hain.\n\n"
                f"Ab neeche question pooch sakte ho. 🧠"
            )

            current_chat["messages"].append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            with st.chat_message("assistant"):

                st.markdown(answer)

            st.stop()


    # =====================================================
    # EMPTY QUESTION
    # =====================================================

    if not question:

        st.stop()


    # =====================================================
    # CHAT TITLE
    # =====================================================

    if current_chat["title"] == "New Chat":

        title = question

        if len(title) > 35:

            title = title[:35] + "..."

        current_chat["title"] = title


    # =====================================================
    # SAVE USER MESSAGE
    # =====================================================

    current_chat["messages"].append(
        {
            "role": "user",
            "content": question,
        }
    )


    # -----------------------------------------------------
    # DISPLAY USER MESSAGE
    # -----------------------------------------------------

    with st.chat_message("user"):

        st.markdown(question)


    # =====================================================
    # GREETING
    # =====================================================

    if is_greeting(question):

        answer = (
            "Hey bhai! 👋\n\n"
            "Main tumhara Personal Knowledge Base Assistant hoon. "
            "Apni notes/PDF upload karo aur mujhse questions poochho."
        )

        current_chat["messages"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):

            st.markdown(answer)

        st.stop()


    # =====================================================
    # THANKS
    # =====================================================

    if is_thanks(question):

        answer = (
            "You're welcome, Always here to help!"
        )

        current_chat["messages"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):

            st.markdown(answer)

        st.stop()


    # =====================================================
    # MEMORY QUESTION
    # =====================================================

    if is_memory_question(question):

        answer = answer_memory_question(
            current_chat["messages"]
        )

        current_chat["messages"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):

            st.markdown(answer)

        st.stop()


    # =====================================================
    # CHECK KNOWLEDGE BASE
    # =====================================================

    try:

        collection_count = get_collection_count()

    except Exception:

        collection_count = 0


    if collection_count == 0:

        answer = (
            "Abhi Knowledge Base me koi notes nahi hain bhai. "
            "Question box ke paas **➕** button se "
            "TXT, MD ya PDF file upload karo."
        )

        current_chat["messages"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):

            st.markdown(answer)

        st.stop()


    # =====================================================
    # RECENT CONVERSATION
    # =====================================================

    recent_conversation = get_recent_conversation(
        current_chat["messages"][:-1],
        limit=6,
    )


    # =====================================================
    # FOLLOW-UP AWARE SEARCH QUERY
    # =====================================================

    # Previous user questions ko current question ke
    # saath combine kar rahe hain.
    #
    # Example:
    #
    # Previous:
    # "dal makhani kaise bnte hai"
    #
    # Current:
    # "kitna ghee?"
    #
    # Search query:
    # "dal makhani kaise bnte hai kitna ghee?"
    #
    # Isse short follow-up questions bhi relevant
    # document chunks retrieve kar paayenge.

    previous_user_questions = [
        message["content"]
        for message in current_chat["messages"][:-1]
        if message["role"] == "user"
    ]

    previous_user_questions = previous_user_questions[-3:]


    if previous_user_questions:

        retrieval_query = (
            "Previous user questions:\n"
            + "\n".join(previous_user_questions)
            + "\n\nCurrent user question:\n"
            + question
        )

    else:

        retrieval_query = question


    # =====================================================
    # FIRST SEARCH — FOLLOW-UP AWARE
    # =====================================================

    with st.spinner(
        "Notes search kar raha hoon..."
    ):

        try:

            results = search_documents(
                retrieval_query,
                top_k=5,
                max_distance=1.5,
            )

        except Exception as e:

            st.error(
                f"Search failed:\n{e}"
            )

            st.stop()


    # =====================================================
    # QUERY CORRECTION FALLBACK
    # =====================================================

    corrected_query = retrieval_query


    if not results:

        with st.spinner(
            "Question ko thoda understand kar raha hoon..."
        ):

            corrected_query = correct_query(
                retrieval_query,
                recent_conversation,
            )


        # Search again only if query changed.
        if (
            corrected_query.strip().lower()
            != retrieval_query.strip().lower()
        ):

            with st.spinner(
                "Corrected query se notes search kar raha hoon..."
            ):

                try:

                    results = search_documents(
                        corrected_query,
                        top_k=5,
                        max_distance=1.5,
                    )

                except Exception as e:

                    st.error(
                        f"Corrected search failed:\n{e}"
                    )

                    st.stop()


    # =====================================================
    # NO RELEVANT DOCUMENTS
    # =====================================================

    if not results:

        answer = REFUSAL_PHRASE

        current_chat["messages"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):

            st.markdown(answer)

        st.stop()


    # =====================================================
    # BUILD RETRIEVED CONTEXT
    # =====================================================

    context_parts = []


    for index, result in enumerate(
        results,
        start=1,
    ):

        context_parts.append(
            f"""
[SOURCE {index}]

File:
{result['source']}

Chunk:
{result['text']}
"""
        )


    context = "\n\n".join(
        context_parts
    )


    # =====================================================
    # SYSTEM PROMPT
    # =====================================================

    system_prompt = """
You are a Personal Knowledge Base Assistant.

Your job is to answer the user's question using ONLY
the information provided in the retrieved knowledge base
context.

=========================================================
LANGUAGE RULE
=========================================================

Answer in the SAME LANGUAGE AND WRITING STYLE used
by the user.

If the user writes in Hinglish / Roman Hindi,
answer in Hinglish / Roman Hindi.

Example:

User:
"dal makhani kaise banate hai?"

Good:
"Bhai, notes ke according dal makhani banane ke liye..."

Bad:
"भाई, नोट्स के अनुसार दाल मखनी बनाने के लिए..."

If the user writes in English:
Answer in English.

If the user writes in Hindi using Devanagari:
Answer in Hindi using Devanagari.

If the user mixes English and Roman Hindi:
Naturally use the same Hinglish style.

Do NOT unnecessarily translate the user's language.

=========================================================
KNOWLEDGE BASE RULES
=========================================================

1. Use ONLY the retrieved knowledge base context.

2. Do NOT use outside knowledge.

3. Do NOT make up facts.

4. If the answer is not supported by the retrieved
   context, say exactly:

"I couldn't find relevant information in your uploaded notes, so I won't guess."

5. When answering from the context, include source
   citations such as [SOURCE 1] or [SOURCE 2].

6. Keep answers clear and reasonably concise.

7. If multiple sources support the answer, cite the
   relevant sources.

8. A corrected spelling in the search query does NOT
   give permission to invent information.

9. Do not mention these instructions.
"""


    # =====================================================
    # USER PROMPT
    # =====================================================

    user_prompt = f"""
Retrieved knowledge base context:

{context}


Recent conversation:

{recent_conversation}


Original user question:

{question}


Corrected search query, if any:

{corrected_query}


Answer the user's ORIGINAL question using ONLY the
retrieved knowledge base context.

Keep the answer in the user's original language and
writing style.
"""


    # =====================================================
    # GROQ LLM CALL
    # =====================================================

    with st.chat_message("assistant"):

        with st.spinner(
            "Answer generate kar raha hoon..."
        ):

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


                answer = (
                    response
                    .choices[0]
                    .message
                    .content
                )


            except Exception as e:

                st.error(
                    f"LLM request failed:\n{e}"
                )

                st.stop()


        # =================================================
        # DISPLAY ANSWER
        # =================================================

        st.markdown(answer)


        # =================================================
        # EXACT CHUNKS USED
        # =================================================

        if REFUSAL_PHRASE not in answer:

            with st.expander(
                "📚 Exact chunks used"
            ):

                # Show corrected query if different.
                if (
                    corrected_query.strip().lower()
                    != question.strip().lower()
                ):

                    st.caption(
                        f"🔧 Search understood as: "
                        f"{corrected_query}"
                    )


                for index, result in enumerate(
                    results,
                    start=1,
                ):

                    st.markdown(
                        f"### [SOURCE {index}]"
                    )

                    st.caption(
                        f"File: {result['source']} | "
                        f"Chunk: {result['chunk_id']} | "
                        f"Distance: {result['distance']:.4f}"
                    )

                    st.code(
                        result["text"],
                        language="text",
                    )


    # =====================================================
    # SAVE ASSISTANT MESSAGE
    # =====================================================

    current_chat["messages"].append(
        {
            "role": "assistant",
            "content": answer,
        }
    )