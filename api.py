from fastapi.middleware.cors import CORSMiddleware
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq

from rag import search_documents


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=GROQ_API_KEY)


app = FastAPI(
    title="Personal Knowledge Base API",
    description="RAG API for the Personal Knowledge Base Assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "Personal Knowledge Base API is running!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    results = search_documents(
        request.question,
        top_k=5
    )

    if not results:
        return {
            "answer": "I couldn't find any relevant information in your uploaded notes.",
            "sources": []
        }

    context = "\n\n".join(
        [
            f"Source: {result.get('source')}\n"
            f"Content:\n{result.get('text')}"
            for result in results
        ]
    )

    prompt = f"""
You are a helpful Personal Knowledge Base Assistant.

Answer the user's question ONLY using the information provided
in the context below.

If the answer is not present in the context, say:
"I couldn't find that information in your uploaded notes."

Do not make up information.

Keep the answer concise and clear.

Context:
{context}

User question:
{request.question}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You answer questions only from the provided knowledge base context."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content

    sources = [
        {
            "source": result.get("source"),
            "chunk_id": result.get("chunk_id"),
            "distance": result.get("distance"),
        }
        for result in results
    ]

    return {
        "answer": answer,
        "sources": sources,
    }