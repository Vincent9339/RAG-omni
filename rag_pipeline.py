import os
import PyPDF2
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import numpy as np
from transformers import pipeline, AutoTokenizer

class PDFLoader:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"PDF file not found at {self.file_path}")
        try:
            with open(self.file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = " ".join([page.extract_text() for page in reader.pages])
                return text
        except Exception as e:
            raise RuntimeError(f"Failed to load PDF: {str(e)}")

class TextChunker:
    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text):
        if not text:
            raise ValueError("Input text cannot be empty")
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            chunks.append(chunk)
        return chunks

class EmbeddingGenerator:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def generate(self, texts):
        if not texts:
            raise ValueError("Input texts cannot be empty")
        return self.model.encode(texts)

class RAGPipeline:
    def __init__(self, model_name="gpt2", generation_config=None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token  # Fix padding warning
        
        self.generator = pipeline(
            "text-generation",
            model=model_name,
            tokenizer=self.tokenizer,
            device=-1  # Use CPU (-1), change to 0 for GPU if available
        )
        
        self.generation_config = generation_config or {
            #"max_length": 150,
            "max_new_tokens":100,
            "do_sample": False,
            "truncation": True,
            "pad_token_id": self.tokenizer.eos_token_id
        }

    def generate_response(self, query, context):
        prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
        
        # Generate with fixed config
        outputs = self.generator(
            prompt,
            **self.generation_config
        )
        
        # Extract and clean response
        full_text = outputs[0]['generated_text']
        answer = full_text.replace(prompt, "").strip()
        return answer.split("\n")[0]  # Return first line only

class VectorStore:
    def __init__(self):
        self.embeddings = None
        self.texts = None
        self.nn = NearestNeighbors(n_neighbors=3, metric='cosine')

    def store(self, embeddings, texts):
        self.embeddings = np.array(embeddings)
        self.texts = texts
        self.nn.fit(self.embeddings)

    def search(self, query_embedding):
        distances, indices = self.nn.kneighbors([query_embedding])
        return [self.texts[i] for i in indices[0]]

def main():
    try:
        #pdf_path = "/visa_rel/pdfs/Visa Code Handbook II_2020_EN.pdf"
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
        
        while True:
            query = input("Enter your question (or 'quit' to exit): ")
            if query.lower() == 'quit':
                break
            
            query_embedding = embedder.generate([query])[0]
            relevant_chunks = vector_store.search(query_embedding)
            context = "\n".join(relevant_chunks)
            
            response = rag.generate_response(query, context)
            print(f"Answer: {response}\n")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
