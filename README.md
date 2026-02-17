# CWP Know-All Agent (RAG Assistant)

An agent that answers questions about **CWP
Academy** using uploaded company documents (PDF + DOCX) with
**citations**.

## Demo (What it does)

-   Ingests company documents into a vector database (Chroma)
-   Chat with an AI assistant in a beautiful UI
-   Answers only from ingested documents (no hallucinations)
-   Shows which sources/chunks were used
-   Includes FAQ quick buttons (Refund, Pricing, Courses, Contact, etc.)

## Tech Stack

-   Python
-   Streamlit (Chat UI)
-   ChromaDB (Vector database)
-   OpenAI Embeddings + Chat Model
-   PyPDF + python-docx

## Features

-   PDF + DOCX ingestion
-   Chunking + embeddings + vector search
-   Chat history
-   FAQ quick buttons
-   Source citations for every answer
-   Beginner-friendly architecture

## Project Structure

    app.py        # Streamlit assistant UI
    ingest.py     # PDF/DOCX ingestion pipeline
    rag.py        # Retrieval + answer generation
    assets/       # assistant image/avatar
    data/         # local data (ignored in GitHub)

## Setup Instructions

### 1. Clone repo

    git clone <YOUR_REPO_URL>
    cd company-rag-agent

### 2. Create environment

    python -m venv .venv
    source .venv/bin/activate   # mac/linux
    # .venv\Scripts\activate  # windows

### 3. Install requirements

    pip install -r requirements.txt

### 4. Add OpenAI key

Create `.env` file:

    OPENAI_API_KEY=your_key_here

### 5. Add documents

Put company docs in:

    data/raw/
      cwp_docs.pdf
      cwp_docs.docx

### 6. Ingest documents

    python ingest.py

### 7. Run assistant

    streamlit run app.py

## 💬 Example Questions

-   What is CWP Academy's refund policy?
-   What courses are offered?
-   What are the pricing plans?
-   How can someone contact CWP Academy?
-   How does enrollment work?

## 🔒 Notes

-   Vector database stored locally in `data/chroma/`
-   `.env` and local data are excluded from GitHub
-   Assistant answers only using provided documents

## 🌟 Future Improvements

-   Upload documents directly from UI
-   Highlight exact evidence used in answers
-   Multi-company support
-   Auth login for internal company usage
-   Deploy to Streamlit Cloud or Render

## 🏷️ Portfolio Use

This project demonstrates: - RAG system design - Vector search
implementation - AI agent architecture - Production-ready UI - Document
intelligence pipelines

Perfect for showcasing AI engineering and LLM application skills.

## 📜 License

MIT
