from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
import requests

# ======= CONFIG =======
PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "n8n_docs"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5
LM_API_URL = "http://localhost:1234/v1/completions"
LM_MODEL = "qwen2.5-7b-instruct"

# ======= LOAD MODELS =======
embedder = SentenceTransformer(EMBED_MODEL)
client = PersistentClient(path=PERSIST_DIR)
collection = client.get_or_create_collection(COLLECTION_NAME)

# ======= MODELS =======
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

# ======= LOGIC =======
def query_docs(question: str):
    if collection.count() == 0:
        return []

    q_embedding = embedder.encode(question, convert_to_numpy=True)
    results = collection.query(
        query_embeddings=[q_embedding.tolist()],
        n_results=TOP_K
    )
    return results['documents'][0]

def check_lm_server():
    try:
        resp = requests.get("http://localhost:1234/v1/models", timeout=5)
        return resp.status_code == 200
    except:
        return False

def generate_answer(question: str, context_chunks):
    if not check_lm_server():
        return "LM Studio server is not running. Please start LM Studio with a model loaded."

    context_text = "\n\n".join(context_chunks)
    prompt = f"""You are an expert n8n assistant. Use ONLY the information provided in the context below to answer the question.
Do not mention or reference any external links, file paths, documentation URLs, or redirect to other sources.
Provide a clear, concise explanation using the actual content from the context provided only.

Context:
{context_text}

Question: {question}

Answer:"""

    payload = {
        "model": LM_MODEL,
        "prompt": prompt,
        "max_new_tokens": 400,
        "temperature": 0.2
    }

    try:
        response = requests.post(LM_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["text"].strip()
    except requests.RequestException as e:
        return f"Error: {str(e)}"

# ======= APP =======
app = FastAPI(title="N8N RAG Chat API", description="Query N8N docs using RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "N8N RAG Chat API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    chunks = query_docs(request.question)
    if not chunks:
        return ChatResponse(answer="No relevant information found in the N8N documentation.")

    answer = generate_answer(request.question, chunks)
    return ChatResponse(answer=answer)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
