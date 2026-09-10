# Personal Knowledge Base Assistant

A beginner-friendly RAG project using:

- Python
- Streamlit
- Groq API for the LLM
- sentence-transformers for local embeddings
- ChromaDB as the local vector database
- pypdf for PDF extraction

## 1. Install Python

Python 3.11

## 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
## 3. Install packages

```bash
pip install -r requirements.txt
```

## 4. Add your Groq API key

```
GROQ_API_KEY=api_key_here
```

## 5. Run

```
streamlit run app.py
```


## 6. Demo

1. Upload `.txt`, `.md`, or `.pdf` notes.
2. Click Index uploaded notes.
3. Ask a question.
4. The app retrieves relevant chunks.
5. Groq answers only from those chunks.
6. The UI shows the exact chunks used.

## Architecture

```text
Notes
  ↓
Text/PDF extraction
  ↓
Overlapping chunks
  ↓
Local embeddings (sentence-transformers)
  ↓
ChromaDB
  ↓
User question
  ↓
Question embedding
  ↓
Top relevant chunks
  ↓
Groq LLM
  ↓
Grounded answer + source citations + exact chunks
```

