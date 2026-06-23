
import json
import os
import re
import numpy as np
import feedparser
import chromadb
from newspaper import Article
from sentence_transformers import SentenceTransformer
from groq import Groq

RSS_URL = "https://techcrunch.com/feed/"
MAX_ARTICLES = 10
CHUNK_SIZE = 200
OVERLAP = 50

def fetch_articles(rss_url, max_articles):
    print("Fetching articles...")
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries[:max_articles]:
        try:
            print(f"  Downloading: {entry.title}")
            article = Article(entry.link)
            article.download()
            article.parse()
            articles.append({
                "title": article.title,
                "url": entry.link,
                "content": article.text
            })
        except Exception as e:
            print(f"  Skipped: {e}")
    return articles

def clean_text(text):
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r" +", " ", text)
    lines = text.split("\n")
    lines = [l.strip() for l in lines if len(l.strip()) > 30]
    return "\n".join(lines).strip()

def chunk_text(text, chunk_size=200, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

def build_pipeline(groq_api_key):
    # Step 1: Fetch
    articles = fetch_articles(RSS_URL, MAX_ARTICLES)
    print(f"Fetched {len(articles)} articles")

    # Step 2: Clean
    cleaned = []
    for a in articles:
        cleaned.append({
            "title": a["title"],
            "url": a["url"],
            "content": clean_text(a["content"])
        })
    print("Cleaned all articles")

    # Step 3: Chunk
    all_chunks = []
    for article in cleaned:
        for i, chunk in enumerate(chunk_text(article["content"])):
            all_chunks.append({
                "chunk_id": str(i),
                "article_title": article["title"],
                "article_url": article["url"],
                "content": chunk
            })
    print(f"Created {len(all_chunks)} chunks")

    # Step 4: Embed
    print("Creating embeddings...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["content"] for c in all_chunks]
    embeddings = embed_model.encode(texts, show_progress_bar=True)
    print("Embeddings created")

    # Step 5: Vector DB
    client_db = chromadb.Client()
    collection = client_db.get_or_create_collection(
        name="tech_news_full",
        metadata={"hnsw:space": "cosine"}
    )
    if collection.count() == 0:
        collection.add(
            ids=[str(i) for i in range(len(all_chunks))],
            embeddings=embeddings.tolist(),
            documents=[c["content"] for c in all_chunks],
            metadatas=[{
                "title": c["article_title"],
                "url": c["article_url"]
            } for c in all_chunks]
        )
    print(f"Vector database ready with {collection.count()} chunks")

    # Step 6: RAG
    groq_client = Groq(api_key=groq_api_key)

    def ask(question):
        query_embedding = embed_model.encode(question).tolist()
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
        print(f"\nQuestion: {question}")
        print(f"\nAnswer: {answer}")
        print(f"\nSources:")
        for url in set(sources):
            print(f"  - {url}")
        return answer

    print("\n RAG News Agent is ready!")
    return ask, cleaned

if __name__ == "__main__":
    api_key = os.getenv("GROQ_API_KEY", "YOUR_GROQ_KEY")
    ask, articles = build_pipeline(api_key)
    ask("What are the biggest tech news today?")
