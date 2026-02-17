import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "company_docs"


# Retrieval
def embed_query(q: str) -> list[float]:
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=q
    )
    return resp.data[0].embedding


def retrieve(query: str, k: int = 5):
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    col = chroma.get_or_create_collection(name=COLLECTION_NAME)

    q_emb = embed_query(query)
    results = col.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return list(zip(docs, metas))


def build_context(hits) -> str:
    """
    IMPORTANT: keep context clean.
    Do NOT include 'Source:' or 'Chunk:' in the context text because the model will echo it.
    We'll show sources in the UI separately.
    """
    blocks = []
    for i, (text, _meta) in enumerate(hits, start=1):
        blocks.append(f"[{i}] {text}")
    return "\n\n".join(blocks)


# System prompt
JSON_SYSTEM_PROMPT = (
    "You are the official CWP Academy assistant.\n"
    "Answer ONLY using the provided context.\n\n"

    "Return ONLY valid JSON in this exact shape:\n"
    "{\n"
    '  "answer_markdown": "string (markdown)",\n'
    '  "citations": ["[1]", "[2]"]\n'
    "}\n\n"

    "FORMATTING RULES:\n"
    "- If the answer is short (one person, one fact, one sentence), respond in a clean natural sentence.\n"
    "- Do NOT use bullet points for simple answers.\n"
    "- If the answer contains multiple items (pricing, features, steps, services, policies), use clean markdown bullets.\n"
    "- Use section headers ONLY when helpful.\n"
    "- Keep responses human, natural, and professional.\n"
    "- Do NOT mention chunks or sources inside the answer text.\n"
    "- Always include citations at the end like [1][2].\n"
    "- If the answer is not in the context, say you don't have that information.\n"
    "- Never invent information.\n"
)


# Straight Answer
def answer(query: str, k: int = 5):
    """
    Returns (json_text, hits)
    """
    hits = retrieve(query, k=k)
    context = build_context(hits)

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": JSON_SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"}
        ],
        temperature=0.2
    )

    return resp.choices[0].message.content, hits


# Streaming answer (JSON tokens) 
def stream_answer(query: str, k: int = 5):
    """
    Generator that yields JSON text token-by-token.
    At the end it returns sources (for UI).
    """
    hits = retrieve(query, k=k)
    context = build_context(hits)

    stream = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": JSON_SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"}
        ],
        temperature=0.2,
        stream=True,
    )

    for event in stream:
        delta = event.choices[0].delta
        if delta and delta.content:
            yield delta.content

    sources = [
        f"[{i}] {meta.get('source')} (chunk {meta.get('chunk')})"
        for i, (_, meta) in enumerate(hits, start=1)
    ]
    return sources
