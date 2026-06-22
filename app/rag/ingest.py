import json
import os
import feedparser
from newspaper import Article

RSS_URL = 'https://techcrunch.com/feed/'
OUTPUT_PATH = 'data/raw/articles.json'
MAX_ARTICLES = 10

def fetch_articles(rss_url, max_articles):
    print(f'Fetching feed: {rss_url}')
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries[:max_articles]:
        try:
            print(f'Downloading: {entry.title}')
            article = Article(entry.link)
            article.download()
            article.parse()
            articles.append({
                'title': article.title,
                'url': entry.link,
                'content': article.text
            })
        except Exception as e:
            print(f'Skipped: {e}')
    return articles

def save_articles(articles, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)
    print(f'Saved {len(articles)} articles to {output_path}')

if __name__ == '__main__':
    articles = fetch_articles(RSS_URL, MAX_ARTICLES)
    save_articles(articles, OUTPUT_PATH)
