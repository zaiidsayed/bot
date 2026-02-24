from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def classify_interest(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify user interest in one word like Music, Coding, Dating, Gaming, Fitness."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()
def check_toxic(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return SAFE or TOXIC."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()