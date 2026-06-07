import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key found: {api_key[:20]}..." if api_key else "❌ No API key")

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Say 'Hello World' only"}],
        max_tokens=10
    )
    print(f" OpenAI API OK: {response.choices[0].message.content}")
except Exception as e:
    print(f"OpenAI Error: {str(e)[:200]}")
