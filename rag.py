from pathlib import Path
import hashlib
import io

import chromadb
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / "chroma_db"
NOTES_DIR = BASE_DIR / "notes"

NOTES_DIR.mkdir(exist_ok=True)

# Small, free local embedding model.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_embedding_model = None
_chroma_client = None
_collection = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _chroma_client.get_or_create_collection(
            name="knowledge_base"
        )
    return _collection


def read_file_bytes(file_obj):
    if hasattr(file_obj, "getvalue"):
        return file_obj.getvalue()
    return Path(file_obj).read_bytes()


def extract_text(filename, data):
    suffix = Path(filename).suffix.lower()

    if suffix in [".txt", ".md"]:
        return data.decode("utf-8", errors="ignore")

    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n\n".join(pages)

    raise ValueError(f"Unsupported file type: {suffix}")


def chunk_text(text, chunk_size=1000, overlap=200):
    """Character-based overlapping chunks.

    We prefer paragraph boundaries where possible, then use overlap so
    information near chunk boundaries is not lost.
    """
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= chunk_size:
            current = f"{current}\n\n{paragraph}".strip()
        else:
            if current:
                chunks.append(current)

            # Keep an overlap from the previous chunk.
            overlap_text = current[-overlap:] if current else ""
            current = f"{overlap_text}\n\n{paragraph}".strip()

            # Very long paragraphs still need hard splitting.
            while len(current) > chunk_size:
                chunks.append(current[:chunk_size])
                current = current[chunk_size - overlap :]

    if current:
        chunks.append(current)

    return chunks


def make_id(source, chunk_index, text):
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
    return f"{source}-{chunk_index}-{digest}"


def ingest_documents(uploaded_files):
    collection = get_collection()
    model = get_embedding_model()

    total_chunks = 0
    total_files = 0

    # Avoid processing the same filename twice in one upload
    processed_files = set()

    for uploaded in uploaded_files:
        filename = Path(uploaded.name).name

        if filename in processed_files:
            continue

        processed_files.add(filename)

        data = read_file_bytes(uploaded)

        # Save original file for demo/local use.
        (NOTES_DIR / filename).write_bytes(data)

        text = extract_text(filename, data)
        chunks = chunk_text(text)

        if not chunks:
            continue

        # Remove older chunks belonging to this same file.
        # This means re-uploading an edited file replaces the old version.
        collection.delete(
            where={"source": filename}
        )

        embeddings = model.encode(
            chunks,
            normalize_embeddings=True
        ).tolist()

        ids = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            ids.append(make_id(filename, i, chunk))

            metadatas.append(
                {
                    "source": filename,
                    "chunk_id": i,
                }
            )

        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        total_files += 1
        total_chunks += len(chunks)

    return {
        "files": total_files,
        "chunks": total_chunks,
    }


def search_documents(question, top_k=5, max_distance=1.5):
    collection = get_collection()

    if collection.count() == 0:
        return []

    model = get_embedding_model()

    query_embedding = model.encode(
        [question],
        normalize_embeddings=True
    ).tolist()[0]

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    items = []

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    for doc, meta, distance in zip(docs, metas, distances):

        # Ignore clearly irrelevant chunks
        if distance > max_distance:
            continue

        items.append(
            {
                "text": doc,
                "source": meta["source"],
                "chunk_id": meta["chunk_id"],
                "distance": distance,
            }
        )

    return items


def get_collection_count():
    return get_collection().count()

def clear_collection():
    global _collection

    if _chroma_client is None:
        get_collection()

    _chroma_client.delete_collection("knowledge_base")
    _collection = None

def ingest_local_notes():
    files = [
        path
        for path in NOTES_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in [".txt", ".md", ".pdf"]
    ]

    if not files:
        return {
            "files": 0,
            "chunks": 0,
        }

    return ingest_documents(files)