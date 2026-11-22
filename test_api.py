import os
from dotenv import load_dotenv
from openai import OpenAI

# Load API key
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Gemini API Key not found!")
else:
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    try:
        response = client.chat.completions.create(
            model="gemini-3.8-flash",
            messages=[
                {
                    "role": "user",
                    "content": "Hello! AI Customer Support is ready."
                }
            ]
        )

        print(response.choices[0].message.content)

    except Exception as e:
        print("API Error:", e)