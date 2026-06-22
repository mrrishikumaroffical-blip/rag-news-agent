from app.rag.ingest import fetch_articles, save_articles
from app.rag.ingest import RSS_URL, OUTPUT_PATH, MAX_ARTICLES

def main():
    articles = fetch_articles(RSS_URL, MAX_ARTICLES)
    save_articles(articles, OUTPUT_PATH)

if __name__ == '__main__':
    main()
