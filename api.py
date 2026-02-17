import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from rag import answer
from ingest import ingest_directory
import json
from sse_starlette.sse import EventSourceResponse
from rag import stream_answer

load_dotenv()

app = FastAPI(
    title="CWP Know-All Agent API",
    version="1.0.0",
    description="RAG API that answers questions about CWP Academy using ingested documents.",
)

class AskStreamRequest(BaseModel):
    question: str = Field(..., min_length=2)
    top_k: int = Field(5, ge=1, le=10)

class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question about CWP Academy")
    top_k: int = Field(5, ge=1, le=10, description="How many chunks to retrieve")

class AskResponse(BaseModel):
    answer: str
    sources: list[str]

class IngestRequest(BaseModel):
    raw_dir: str = Field("data/raw", description="Directory containing PDF/DOCX/TXT files")
    batch_size: int = Field(64, ge=8, le=256)
    max_pages: int | None = Field(None, description="Optional PDF page limit for testing")

@app.get("/health")
def health():
    ok = bool(os.getenv("OPENAI_API_KEY"))
    return {"status": "ok", "has_openai_key": ok}

@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        ingest_directory(raw_dir=req.raw_dir, batch_size=req.batch_size, max_pages=req.max_pages)
        return {"status": "ok", "message": f"Ingested documents from {req.raw_dir}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        # NOTE: your rag.answer currently retrieves k=5 internally.
        # If you want top_k configurable, we’ll patch rag.py next.
        response, hits = answer(req.question, k=req.top_k)
        sources = [f"{meta.get('source')} (chunk {meta.get('chunk')})" for _, meta in hits]
        return {"answer": response, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ask-stream")
def ask_stream(req: AskStreamRequest):
    """
    Streams the assistant response token-by-token using Server-Sent Events (SSE).
    Frontend receives events in real time.
    """

    def event_generator():
        # stream tokens
        gen = stream_answer(req.question, k=req.top_k)

        # stream_answer yields tokens, but we also want sources at the end
        sources = None
        try:
            while True:
                token = next(gen)
                yield {"event": "token", "data": json.dumps(token)}
        except StopIteration as stop:
            # stream_answer returns sources via "return sources"
            sources = stop.value

        # send final event with sources
        yield {"event": "sources", "data": json.dumps(sources or [])}

        # tell client we are done
        yield {"event": "done", "data": json.dumps("")}

    return EventSourceResponse(event_generator())
