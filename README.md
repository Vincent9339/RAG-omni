# RAG-Omni

RAG-Omni is an end-to-end Retrieval-Augmented Generation (RAG) system designed to turn static PDF documents into an interactive, QA chatbot.


Instead of relying solely on a language model’s limited internal knowledge, this project combines:

**Document ingestion**: a PDF is parsed into clean text.
**Chunking**: the text is split into smaller segments for efficient search.
**Semantic embeddings**: each chunk is embedded into a numerical vector space.
**Vector search**: at query time, the system finds the most relevant chunks.
**LLM generation**: the retrieved context is injected into a language model (GPT by default) to generate a context-aware answer.

The result is a lightweight, extensible RAG pipeline that can answer natural language questions directly from the contents of your documents. It exposes a Flask API for easy integration with frontends, enterprise workflows, or other applications.

This project serves both as a reference implementation of a custom RAG system and as a starting point for building more advanced document-grounded chatbots.

## Features

**End-to-end RAG pipeline**: from raw document ingestion to question answering, all components are integrated and ready to run.
**PDF knowledge base**: load any PDF and automatically preprocess it into retrievable text segments.
**Semantic retrieval**: query embeddings and vector similarity search ensure responses are grounded in the most relevant parts of the document.
**LLM-backed generation**: answers are produced by a Hugging Face language model (default: GPT-2), conditioned on retrieved context.
**Modular design**: each component (loader, chunker, embeddings, vector store, generator) is implemented as an independent class, making it easy to replace or extend.
**API-first architecture**: exposes a clean Flask REST API (/api/ask) for integration with web frontends or external systems.
**Configurable generation**: parameters such as token limits, temperature, and sampling strategy can be tuned via app.py.

## Usage
### Endpoint
**POST /api/ask**
**Request:**
```
{
  "question": "What are the compliance requirements mentioned in the document?"
}
```
**Response**
```
{
  "answer": "The document describes compliance requirements including ...",
  "context": [
    "Relevant chunk 1 ...",
    "Relevant chunk 2 ..."
  ]
}
```
## Tech Stack

- Python 3.9+
- Flask (API server)
- Hugging Face Transformers
- GPT for response generation (default model)
- AutoTokenizer for preprocessing
- PyTorch (model inference backend)
- PDF parsing library (used in PDFLoader)


## License

This project is licensed under the MIT License.
