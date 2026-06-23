
import requests
from groq import Groq

def generate_linkedin_post(articles, groq_client):
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
        print(f"Error: {response.status_code}")
        print(response.json())
