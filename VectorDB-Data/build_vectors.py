#!/usr/bin/env python3
# build_vectors.py

import os
import sys
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import chromadb
from chromadb.config import Settings

# ---------------- CONFIG ----------------
DOCS_TXT = "n8n_docs.txt"
PERSIST_DIR = "chroma_db"          # folder to store vector DB
COLLECTION_NAME = "n8n_docs"
CHUNK_SIZE = 500                    # smaller chunks to save memory
CHUNK_OVERLAP = 100
EMBED_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 64

# ------------- CHUNKING FUNCTION -------------
def chunk_file(file_path, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Yield chunks of text from a file to avoid memory issues."""
    buffer = ""
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            buffer += line
            while len(buffer) >= chunk_size:
                yield buffer[:chunk_size]
                buffer = buffer[chunk_size - overlap:]
    if buffer:
        yield buffer

# ------------- MAIN FUNCTION -------------
def main():
    if not os.path.exists(DOCS_TXT):
        print(f"ERROR: {DOCS_TXT} not found. Put it in the same folder as this script.")
        sys.exit(1)

    print("Loading embedding model...")
    embedder = SentenceTransformer(EMBED_MODEL)

    # Create persistent Chroma client
    client = chromadb.Client(Settings(persist_directory=PERSIST_DIR))

    # Delete existing collection if present
    if COLLECTION_NAME in [c['name'] for c in client.list_collections()]:
        print(f"Existing collection '{COLLECTION_NAME}' found — deleting to recreate fresh...")
        client.delete_collection(COLLECTION_NAME)

    # Create a new collection
    collection = client.create_collection(name=COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' created successfully.")

    # Process file in streaming batches
    batch_docs, batch_ids, batch_meta = [], [], []
    for i, chunk in enumerate(tqdm(chunk_file(DOCS_TXT), desc="Chunking & batching")):
        batch_docs.append(chunk)
        batch_ids.append(f"n8n_{i}")
        batch_meta.append({"source": "n8n_docs", "chunk_index": i})

        if len(batch_docs) == BATCH_SIZE:
            embeddings = embedder.encode(batch_docs, show_progress_bar=False, convert_to_numpy=True)
            collection.add(documents=batch_docs, ids=batch_ids, metadatas=batch_meta, embeddings=embeddings.tolist())
            batch_docs, batch_ids, batch_meta = [], [], []

    # Add remaining chunks
    if batch_docs:
        embeddings = embedder.encode(batch_docs, show_progress_bar=False, convert_to_numpy=True)
        collection.add(documents=batch_docs, ids=batch_ids, metadatas=batch_meta, embeddings=embeddings.tolist())

    print(f"Done. Vector DB is saved in: {PERSIST_DIR}")

# ------------- RUN -------------
if __name__ == "__main__":
    main()
