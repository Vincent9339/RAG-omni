# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from rag_pipeline import PDFLoader, TextChunker, EmbeddingGenerator, VectorStore, RAGPipeline

app = Flask(__name__)
CORS(app)

# Initialize components
pdf_path = "general_schengen_visa_requirments.pdf"
loader = PDFLoader(pdf_path)
text = loader.load()
chunker = TextChunker()
chunks = chunker.chunk(text)
embedder = EmbeddingGenerator()
embeddings = embedder.generate(chunks)
vector_store = VectorStore()
vector_store.store(embeddings, chunks)
rag = RAGPipeline()

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        query = data['question']
        
        query_embedding = embedder.generate([query])[0]
        relevant_chunks = vector_store.search(query_embedding)
        context = "\n".join(relevant_chunks)
        
        response = rag.generate_response(query, context)
        return jsonify({"answer": response})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
    

