
import chromadb
import json
import numpy as np
from sentence_transformers import SentenceTransformer

def load_data():
    with open("data/processed/chunks.json") as f:
        chunks = json.load(f)
    embeddings = np.load("data/processed/embeddings.npy")
    return chunks, embeddings

def build_vector_db(chunks, embeddings):
    client = chromadb.Client()
    collection = client.create_collection(
        name="tech_news",
        metadata={"hnsw:space": "cosine"}
    )
    collection.add(
        ids=[str(i) for i in range(len(chunks))],
        embeddings=embeddings.tolist(),
        documents=[chunk["content"] for chunk in chunks],
        metadatas=[{
            "title": chunk["article_title"],
            "url": chunk["article_url"]
        } for chunk in chunks]
    )
    print(f"Vector database ready with {collection.count()} chunks!")
    return collection

def search(query, collection, model, n_results=3):
    query_embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results

if __name__ == "__main__":
    print("Loading data...")
    chunks, embeddings = load_data()
    
    print("Loading model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Building vector database...")
    collection = build_vector_db(chunks, embeddings)
    
    query = "What companies laid off employees because of AI?"
    print(f"\nSearching: {query}")
    results = search(query, collection, model)
    
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        print(f"\nResult {i+1}: {meta['title']}")
        print(doc[:200])
