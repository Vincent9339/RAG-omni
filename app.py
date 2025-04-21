import os
import socket
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from rag_pipeline import PDFLoader, TextChunker, EmbeddingGenerator, VectorStore, RAGPipeline

# Configuration
CONFIG = {
    "host": "0.0.0.0",
    "start_port": 5000,
    "max_port_attempts": 20,
    "pdf_path": "document.pdf",
    "static_folder": "static",
    "generation_config": {
        "max_length": 200,
        "do_sample": False,
        "truncation": True,
        "pad_token_id": 50256  # GPT2's eos_token_id
    }
}

# Initialize Flask app
app = Flask(__name__, static_folder=CONFIG["static_folder"])
CORS(app)

# Initialize RAG components with enhanced error handling
def initialize_components():
    try:
        print("🔄 Initializing RAG pipeline...")
        
        # 1. Load and chunk document
        loader = PDFLoader(CONFIG["pdf_path"])
        text = loader.load()
        if not text.strip():
            raise ValueError("Extracted text is empty - check PDF content")
            
        chunker = TextChunker()
        chunks = chunker.chunk(text)
        print(f"📄 Loaded {len(chunks)} text chunks from PDF")
        
        # 2. Initialize embeddings
        embedder = EmbeddingGenerator()
        embeddings = embedder.generate(chunks)
        
        # 3. Setup vector store
        vector_store = VectorStore()
        vector_store.store(embeddings, chunks)
        
        # 4. Initialize LLM with proper config
        rag = RAGPipeline(generation_config=CONFIG["generation_config"])
        print("✅ RAG pipeline initialized successfully")
        
        return {
            "vector_store": vector_store,
            "embedder": embedder,
            "rag": rag,
            "status": "ready",
            "chunks": chunks
        }
        
    except Exception as e:
        print(f"❌ Failed to initialize RAG pipeline: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

components = initialize_components()

# API Endpoints
@app.route('/api/ask', methods=['POST'])
def handle_query():
    if components["status"] != "ready":
        return jsonify({
            "error": "System not ready",
            "details": components.get("message")
        }), 503
    
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"error": "Missing question parameter"}), 400
        
        question = data['question']
        print(f"🔍 Processing question: '{question}'")
        
        # Generate query embedding
        query_embedding = components["embedder"].generate([question])[0]
        
        # Find relevant context
        relevant_chunks = components["vector_store"].search(query_embedding)
        context = "\n".join(relevant_chunks)
        
        # Generate response with proper error handling
        try:
            response = components["rag"].generate_response(question, context)
            return jsonify({
                "answer": response,
                "context": relevant_chunks
            })
        except Exception as e:
            print(f"🤖 Generation error: {str(e)}")
            return jsonify({
                "error": "Answer generation failed",
                "details": str(e)
            }), 500
            
    except Exception as e:
        print(f"⚠️ API error: {str(e)}")
        return jsonify({
            "error": "Processing failed",
            "details": str(e)
        }), 500

# Static file serving
@app.route('/')
def serve_index():
    return send_from_directory(CONFIG["static_folder"], 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(CONFIG["static_folder"], filename)

# Server utilities
def find_available_port():
    for port in range(CONFIG["start_port"], CONFIG["start_port"] + CONFIG["max_port_attempts"]):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((CONFIG["host"], port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available ports found")

if __name__ == '__main__':
    port = find_available_port()
    print(f"\n🚀 Server running on http://{CONFIG['host']}:{port}")
    print(f"📂 Serving static files from {os.path.abspath(CONFIG['static_folder'])}")
    print(f"📄 Using PDF document: {os.path.abspath(CONFIG['pdf_path'])}")
    app.run(host=CONFIG["host"], port=port, debug=False)  # debug=False for production
