import os
import requests
import json
from datetime import datetime

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
TOPICS_FILE  = "data/night_topics.json"

# Learning journey topics - simple to complex over time
TOPICS = [
    # Week 1 - Basics
    "Excel VLOOKUP function for data analysts",
    "What is a pivot table and how to use it",
    "Basic SQL SELECT queries every analyst needs",
    "How to clean messy data in Excel",
    "Understanding data types in analytics",
    "What is data analysis and why it matters",
    "How to make your first bar chart",
    # Week 2 - Python basics
    "Python Pandas read_csv for beginners",
    "How to filter data using Pandas",
    "Groupby in Pandas explained simply",
    "Handling missing values in Python",
    "Basic data visualization with Matplotlib",
    "How to merge two dataframes in Pandas",
    "Python list comprehensions for analysts",
    # Week 3 - SQL
    "SQL JOIN types every analyst must know",
    "GROUP BY and HAVING in SQL",
    "SQL subqueries explained simply",
    "Window functions in SQL",
    "How to write efficient SQL queries",
    "SQL vs Python - when to use which",
    "Creating views in SQL",
    # Week 4 - Advanced
    "Building a dashboard in Power BI",
    "A/B testing basics for data analysts",
    "Understanding statistical significance",
    "How to present data insights to stakeholders",
    "Common data analyst interview questions",
    "Building your data analyst portfolio",
    "How AI is changing data analytics",
]

def get_todays_topic():
    """Pick topic based on day number to progress over time."""
    os.makedirs("data", exist_ok=True)

    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE) as f:
            data = json.load(f)
        day = data.get("day", 0)
    else:
        day = 0

    topic = TOPICS[day % len(TOPICS)]

    # Save next day
    with open(TOPICS_FILE, "w") as f:
        json.dump({"day": day + 1, "last_topic": topic}, f)

    return topic, day + 1

def call_groq(prompt):
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    return response.json()["choices"][0]["message"]["content"]

def generate_night_post(topic, day_num):
    prompt = f"""You are Rishi Kumar, a data analyst sharing your learning journey on LinkedIn.

Today is Day {day_num} of your data analytics learning journey.
Today's topic: {topic}

Write a LinkedIn post as if YOU are personally learning this today.

Rules:
- Start with "🌙 Day {day_num} of my Data Analytics Journey"
- Write in FIRST PERSON as Rishi Kumar
- Sound genuine and personal like a real learner
- Share what you learned today about: {topic}
- Include 1-2 practical tips or examples
- Mention a struggle or challenge you faced
- End with encouragement for others learning data analytics
- End with hashtags: #DataAnalytics #LearningJourney #DataScience #Python #SQL
- Max 1300 characters
- Conversational and authentic tone
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
        print("✅ Night post published!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    print("🌙 Starting Night Post...")
    topic, day_num = get_todays_topic()
    print(f"  Today's topic: {topic}")
    print(f"  Day number: {day_num}")

    post = generate_night_post(topic, day_num)
    print("\nGenerated Post:")
    print("─" * 40)
    print(post)
    print("─" * 40)
    post_to_linkedin(post)
