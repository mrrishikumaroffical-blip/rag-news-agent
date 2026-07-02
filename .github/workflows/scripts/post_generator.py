import os
import json
import re
from groq import Groq
import requests
from urllib.parse import parse_qs

# Parse issue body
issue_body = os.getenv("ISSUE_BODY", "")
issue_number = os.getenv("ISSUE_NUMBER", "")
repo = os.getenv("REPO", "")

# Extract fields from markdown form
def extract_field(body, field_name):
    pattern = rf"### {field_name}\n\n(.*?)(?=\n### |\Z)"
    match = re.search(pattern, body, re.DOTALL)
    return match.group(1).strip() if match else ""

pillar = extract_field(issue_body, "Post type").strip()
what_did = extract_field(issue_body, "What did you do or learn?").strip()
what_hard = extract_field(issue_body, "What was hard or surprising?").strip()
your_take = extract_field(issue_body, "Your take or opinion").strip()

# Groq prompts by pillar
prompts = {
    "Build Log": f"""You are Rishi Kumar, an AI Data Analyst learning in public.
Raw notes: what I did: {what_did}. what was hard: {what_hard}. my take: {your_take}

Write a LinkedIn post that:
- Opens with a specific learning moment (e.g., "Day X of learning...")
- Includes the exact problem and how you fixed it
- Add 3 bullet points of what you learned
- End by tying it to teaching (if relevant) or your next step
- Keep it human, not polished. Use short sentences. One specific number or tool name.
- Avoid: "it's not X, it's Y" constructs, generic enthusiasm, same closing every time
- Add 3-5 relevant hashtags
- Total: 150-200 words

Write only the post, no preamble.""",

    "Industry Take": f"""You are Rishi Kumar, an AI Data Analyst.
Your opinion: {your_take}

Write a LinkedIn post that:
- Start with a recent AI/data news hook (keep brief)
- State your unique opinion clearly (not neutral)
- Add 1 specific insight or contrarian view
- End with a question or call-to-action
- Keep it human. One specific number or detail. Your real take, not generic analysis.
- Avoid formulaic patterns
- Add 3-5 hashtags
- Total: 120-180 words

Write only the post, no preamble.""",

    "Build-in-Public": f"""You are Rishi Kumar building automation projects.
What I did: {what_did}
My take: {your_take}

Write a LinkedIn post that:
- Show the project name and what it does (RAG agent, YouTube pipeline, etc)
- One specific technical detail or blocker you solved
- Keep tone casual, insider (not tutorial)
- Add 1 lesson learned
- End with next steps
- One specific tool or number
- Human voice, short sentences
- Add 3-5 hashtags
- Total: 130-190 words

Write only the post, no preamble.""",

    "Pivot Story": f"""You are Rishi Kumar (ex-English tutor, now data analyst).
Your story: {your_take}

Write a LinkedIn post that:
- Start with the contrast (teaching English vs. building AI/data systems)
- Show what skills transfer
- Keep it brief, authentic
- One specific parallel or lesson
- End with why it matters now
- Human, reflective tone
- Add 3-5 hashtags
- Total: 120-170 words

Write only the post, no preamble.""",

    "Weekly Wrap": f"""You are Rishi Kumar.
This week: {what_did}
Hard part: {what_hard}
My take: {your_take}

Write a LinkedIn post that:
- Recap your week (3-4 key things)
- One honest reflection (what went well, what didn't)
- A small lesson or realization
- What's next week
- Avoid false positivity
- Human, real tone
- Add 3-5 hashtags
- Total: 140-200 words

Write only the post, no preamble."""
}

# Get Groq prompt
groq_prompt = prompts.get(pillar, prompts["Build Log"])

# Call Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
response = client.chat.completions.create(
    model="mixtral-8x7b-32768",
    messages=[{"role": "user", "content": groq_prompt}],
    temperature=0.7,
    max_tokens=500
)

post_text = response.choices[0].message.content.strip()

# Post to LinkedIn
linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
headers = {
    "Authorization": f"Bearer {linkedin_token}",
    "Content-Type": "application/json"
}

payload = {
    "commentary": post_text,
    "visibility": "PUBLIC"
}

url = "https://api.linkedin.com/v2/ugcPosts"
result = requests.post(url, json=payload, headers=headers)

if result.status_code in [200, 201]:
    print(f"✓ Posted to LinkedIn. Issue #{issue_number}")
else:
    print(f"✗ LinkedIn post failed: {result.status_code} {result.text}")
    exit(1)
