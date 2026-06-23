
import os
import re
import json
import numpy as np
import feedparser
import chromadb
import requests
from newspaper import Article
from sentence_transformers import SentenceTransformer
from groq import Groq

# Config
RSS_URL = "https://techcrunch.com/feed/"
MAX_ARTICLES = 10
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_USER_ID = os.getenv("LINKEDIN_USER_ID")

def fetch_articles(rss_url, max_articles):
    print("Fetching articles...")
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries[:max_articles]:
        try:
            article = Article(entry.link)
            article.download()
            article.parse()
            articles.append({
                "title": article.title,
                "url": entry.link,
                "content": article.text
            })
            print(f"  Downloaded: {article.title}")
        except Exception as e:
            print(f"  Skipped: {e}")
    return articles

def clean_text(text):
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r" +", " ", text)
    lines = text.split("\n")
    lines = [l.strip() for l in lines if len(l.strip()) > 30]
    return "\n".join(lines).strip()

def generate_post(articles, groq_client):
    top5 = articles[:5]
    articles_text = ""
    for i, a in enumerate(top5):
        articles_text += f"{i+1}. {a['title']}\n   {a['url']}\n\n"

    prompt = f"""You are a professional tech news curator.
Create an engaging LinkedIn post summarizing these top 5 tech news stories.
Make it professional, insightful and end with relevant hashtags.
Include the article links.

Articles:
{articles_text}

Write the LinkedIn post:"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def post_to_linkedin(post_content, access_token, user_id):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    post_data = {
        "author": f"urn:li:person:{user_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_content},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=post_data
    )
    if response.status_code == 201:
        print("Posted to LinkedIn successfully!")
        print(f"Post ID: {response.headers.get('x-restli-id')}")
    else:
        print(f"Error posting: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    print("Starting daily pipeline...")

    # Step 1: Fetch and clean
    articles = fetch_articles(RSS_URL, MAX_ARTICLES)
    cleaned = [{"title": a["title"], "url": a["url"], "content": clean_text(a["content"])} for a in articles]
    print(f"Fetched {len(cleaned)} articles")

    # Step 2: Generate LinkedIn post
    groq_client = Groq(api_key=GROQ_API_KEY)
    post = generate_post(cleaned, groq_client)
    print("\nGenerated post:")
    print(post)

    # Step 3: Post to LinkedIn
    post_to_linkedin(post, LINKEDIN_ACCESS_TOKEN, LINKEDIN_USER_ID)
    print("\nDone!")
