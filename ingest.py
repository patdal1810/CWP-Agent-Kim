import os
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document
import chromadb
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "company_docs"
SUPPORTED_EXTS = (".pdf", ".docx", ".txt")

# Readers
def read_pdf_text(path: str, max_pages: int | None = None) -> str:
    reader = PdfReader(path)
    pages = reader.pages if max_pages is None else reader.pages[:max_pages]
    texts = []
    for page in pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts).strip()

def read_docx_text(path: str) -> str:
    doc = Document(path)
    parts = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t:
            parts.append(t)
    return "\n".join(parts).strip()

def read_text_file(path: str) -> str:
    # Optional: supports .txt if you drop them in data/raw/
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()

# Chunking (safe) 
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150):
    text = (text or "").strip()
    if not text:
        return []

    overlap = min(overlap, chunk_size - 1)
    chunks = []

    start = 0
    n = len(text)

    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end == n:
            break

        start = max(0, end - overlap)
        if start >= end:
            start = end

    return chunks

# Embeddings
def embed_batch(texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in resp.data]

# Ingest
def ingest_file(path: str, batch_size: int = 64, max_pages: int | None = None):
    ext = os.path.splitext(path)[1].lower()
    base = os.path.basename(path)

    print(f"\nReading: {path}")

    if ext == ".pdf":
        doc_text = read_pdf_text(path, max_pages=max_pages)
    elif ext == ".docx":
        doc_text = read_docx_text(path)
    elif ext == ".txt":
        doc_text = read_text_file(path)
    else:
        print(f"--- Skipping unsupported file type: {base}")
        return

    if not doc_text:
        print(f"--- No text extracted from {base}. (Is it scanned or empty?)")
        return

    chunks = chunk_text(doc_text)
    print(f"🔹 Total chunks: {len(chunks)}")

    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    col = chroma.get_or_create_collection(name=COLLECTION_NAME)

    for start in range(0, len(chunks), batch_size):
        end = min(len(chunks), start + batch_size)
        batch = chunks[start:end]
        embeddings = embed_batch(batch)

        ids = [f"{base}::chunk_{i}" for i in range(start, end)]
        metadatas = [{"source": base, "chunk": i} for i in range(start, end)]

        col.add(ids=ids, documents=batch, embeddings=embeddings, metadatas=metadatas)
        print(f"Embedded & stored chunks {start}–{end-1}")

    print(f"Done ingesting: {base}")




def ingest_path(path: str, batch_size: int = 64, max_pages: int | None = None):
    """Ingest a single file by path."""
    ingest_file(path, batch_size=batch_size, max_pages=max_pages)

def ingest_directory(raw_dir: str = "data/raw", batch_size: int = 64, max_pages: int | None = None):
    """Ingest all supported files in a directory."""
    files = [
        f for f in os.listdir(raw_dir)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS
    ]
    if not files:
        raise ValueError(f"No supported files found in {raw_dir}")

    for f in files:
        ingest_file(os.path.join(raw_dir, f), batch_size=batch_size, max_pages=max_pages)

if __name__ == "__main__":
    raw_dir = "data/raw"

    # For fast api
    ingest_directory(raw_dir="data/raw", batch_size=64, max_pages=None)

    files = [
        f for f in os.listdir(raw_dir)
        if os.path.splitext(f)[1].lower() in (".pdf", ".docx", ".txt")
    ]

    if not files:
        raise SystemExit("No .pdf, .docx, or .txt files found in data/raw/")

    # Ingest all supported files found
    for f in files:
        ingest_file(os.path.join(raw_dir, f), batch_size=64, max_pages=None)
