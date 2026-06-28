import os
import requests
import feedparser

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://venturebeat.com/feed/",
]

def call_groq(prompt):
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    return response.json()["choices"][0]["message"]["content"]

def fetch_news():
    articles = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.get("title", ""),
                "url":   entry.get("link", ""),
            })
    return articles[:10]

def generate_morning_post(articles):
    news_text = ""
    for i, a in enumerate(articles[:5]):
        news_text += f"{i+1}. {a['title']}\n   {a['url']}\n\n"

    prompt = f"""You are a professional tech news curator on LinkedIn.

Write a morning LinkedIn post summarizing top AI and tech news.

News:
{news_text}

Rules:
- Start with "🌅 Good Morning! Here's your AI & Tech News Roundup"
- Summarize each story in 1-2 sentences
- Professional but engaging tone
- End with 5 relevant hashtags
- Max 1300 characters
- Include links
"""
    return call_groq(prompt)

def post_to_linkedin(content):
    token   = os.getenv("LINKEDIN_ACCESS_TOKEN")
    user_id = os.getenv("LINKEDIN_USER_ID")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    data = {
        "author": f"urn:li:person:{user_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
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
        json=data
    )
    if response.status_code == 201:
        print("✅ Morning post published!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    print("🌅 Starting Morning Post...")
    articles = fetch_news()
    post     = generate_morning_post(articles)
    print("\nGenerated Post:")
    print("─" * 40)
    print(post)
    print("─" * 40)
    post_to_linkedin(post)
