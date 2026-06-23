
import json
import numpy as np
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

def build_rag_system(groq_api_key):
    with open("data/processed/chunks.json") as f:
        all_chunks = json.load(f)

    embeddings = np.load("data/processed/embeddings.npy")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client_db = chromadb.Client()
    collection = client_db.get_or_create_collection(
        name="tech_news",
        metadata={"hnsw:space": "cosine"}
    )

    if collection.count() == 0:
        collection.add(
            ids=[str(i) for i in range(len(all_chunks))],
            embeddings=embeddings.tolist(),
            documents=[chunk["content"] for chunk in all_chunks],
            metadatas=[{
                "title": chunk["article_title"],
                "url": chunk["article_url"]
            } for chunk in all_chunks]
        )

    groq_client = Groq(api_key=groq_api_key)

    def ask(question):
        query_embedding = model.encode(question).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        context = ""
        sources = []
        for i in range(3):
            context += results["documents"][0][i] + "\n\n"
            sources.append(results["metadatas"][0][i]["url"])

        prompt = f"""You are a tech news assistant.
Answer the question using only the context below.
Be concise and clear.

Context:
{context}

Question: {question}

Answer:"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content
        print(f"Question: {question}")
        print(f"\nAnswer: {answer}")
        print(f"\nSources:")
        for url in set(sources):
            print(f"  - {url}")

    return ask

if __name__ == "__main__":
    import os
    api_key = os.getenv("GROQ_API_KEY")
    ask = build_rag_system(api_key)
    ask("What companies laid off employees because of AI?")
