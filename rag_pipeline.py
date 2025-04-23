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
    def __init__(self, chunk_size=350, overlap=100):
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
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Default generation config optimized for RAG
        self.generation_config = {
            "max_new_tokens": 100,       # Only generate up to 150 new tokens
            "do_sample": False,          # Disabled sampling for deterministic answers
            "truncation": "only_first",  # Only truncate the context, not the question
            "pad_token_id": self.tokenizer.eos_token_id,
            "no_repeat_ngram_size": 2,    # Prevent word repetition
            "repetition_penalty": 1.5 
        }
        
        if generation_config:
            self.generation_config.update(generation_config)
        
        # Remove temperature if not sampling
        if not self.generation_config.get("do_sample", False):
            self.generation_config.pop("temperature", None)
        
        self.generator = pipeline(
            "text-generation",
            model=model_name,
            tokenizer=self.tokenizer,
            device=-1
        )
        self.max_model_length = 1024  # GPT-2's limit

    def generate_response(self, query, context):
        # 1. Create prompt with smart truncation
        #prompt = self._build_prompt(query, context)
        prompt = (
            "Answer the question based on the context below. "
            "If you don't know the answer, say 'I don't know'.\n\n"
            f"Context: {context}\n\n"
            f"Question: {query}\n"
            "Answer:"
        )
        
        try:
            # 2. Generate response
            outputs = self.generator(
                prompt,
                **self.generation_config
            )
            full_response = outputs[0]['generated_text']
            answer = full_response.split("Answer:")[1].strip()
            #return full_text.replace(prompt, "").strip().split("\n")[0]
            if answer.lower().startswith(("the question is", "the word", "what does")):
                return "I don't know"  # Fallback for bad generations
            return answer
        except Exception as e:
            print(f"⚠️ Generation error: {str(e)}")
            return "I couldn't generate a response. Please try a more specific question."

    def _build_prompt(self, query, context):
        """Builds a prompt that fits within model limits"""
        base_prompt = f"\n\nQuestion: {query}\n\nAnswer:"
        max_context_length = self.max_model_length - len(self.tokenizer.tokenize(base_prompt))
        
        # Tokenize context and truncate if needed
        context_tokens = self.tokenizer.tokenize(context)
        if len(context_tokens) > max_context_length:
            print(f"⚠️ Truncating context from {len(context_tokens)} to {max_context_length} tokens")
            context_tokens = context_tokens[:max_context_length]
        
        truncated_context = self.tokenizer.convert_tokens_to_string(context_tokens)
        return f"Context: {truncated_context}{base_prompt}"

class VectorStore:
    def __init__(self, tokenizer=None):
        self.embeddings = None
        self.texts = None
        self.nn = NearestNeighbors(n_neighbors=3, metric='cosine')
        self.tokenizer = tokenizer  # Store the tokenizer reference

    def store(self, embeddings, texts):
        self.embeddings = np.array(embeddings)
        self.texts = texts
        self.nn.fit(self.embeddings)

    def search(self, query_embedding, max_tokens=500):
        distances, indices = self.nn.kneighbors([query_embedding])
        
        if not self.tokenizer:
            return [self.texts[i] for i in indices[0][:3]]  # Fallback without token counting
            
        selected_chunks = []
        current_length = 0
        
        for i in indices[0]:
            chunk = self.texts[i]
            chunk_length = len(self.tokenizer.tokenize(chunk))
            if current_length + chunk_length > max_tokens:
                break
            selected_chunks.append(chunk)
            current_length += chunk_length
        
        return selected_chunks
        
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
