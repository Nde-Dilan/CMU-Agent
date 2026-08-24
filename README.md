# CMU Student Support Agent (MVP)

## Overview

This project is an AI-powered student support assistant that answers questions using official CMU documents.

The goal of the MVP is to demonstrate a local Retrieval-Augmented Generation (RAG) system that provides grounded responses instead of relying only on an LLM's general knowledge.

---

## MVP Objectives

- Answer questions using official CMU documents.
- Run completely locally using free tools.
- Demonstrate a working RAG pipeline.
- Build a simple interface for the demo.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| LLM | Qwen3:8B (Ollama) |
| Backend | FastAPI |
| Embeddings | nomic-embed-text *(planned)* |
| Vector Database | ChromaDB *(planned)* |
| Frontend | Streamlit *(planned)* |

---

## Current Progress

### Completed

- Repository cloned
- Development branch created
- Python 3.11 environment configured
- Ollama installed
- Qwen3:8B downloaded
- Backend dependencies installed
- Initial project structure created

### Next Step

Implement the connection between Python and the local Qwen model.

---

## Development Philosophy

The project is developed one working layer at a time.

```
Python
   ↓
Qwen
   ↓
FastAPI
   ↓
RAG
   ↓
Streamlit Demo
```

Each layer is tested before moving to the next.

---

## Project Structure

```text
backend/
│
├── app/
│   ├── chatbot/
│   ├── config.py
│   └── main.py
│
├── requirements.txt
└── .env
```