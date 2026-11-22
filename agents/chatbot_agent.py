import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Groq API Connection
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    timeout=30.0
)


def chatbot_reply(user_message, chat_history=None):

    if chat_history is None:
        chat_history = []

    messages = [
        {
            "role": "system",
            "content": """
            You are a friendly, professional AI Customer Support Assistant.

            Your responsibilities:
            - Help with orders, refunds, replacements, damaged products,
              and general customer support.
            - Respond politely, clearly, and in simple language.

            CONVERSATION MEMORY RULES:
            - Remember all information the customer shared earlier
              in the current conversation.
            - Use previous messages as context for every response.
            - Never ask for information that the customer already provided.
            - If the customer gave an order number earlier, remember it
              and refer to it in later messages.
            - If the customer asks about their order, use the previously
              provided order number when available.
            - Remember the customer's complaint or refund reason.

            ORDER AND REFUND RULES:
            - Never invent order details or tracking information.
            - Do not claim to access live order tracking unless connected
              to the order database.
            - Never claim a refund or replacement has been approved
              unless the system confirms it.
            - If information is unavailable, explain honestly and guide
              the customer to the appropriate feature.

            Be conversational and avoid repeating questions.
            """
        }
    ]

    messages.extend(chat_history)

    messages.append({
        "role": "user",
        "content": user_message
    })

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages
        )

        return response.choices[0].message.content

    except Exception as e:

        error_message = str(e)
        print("Groq API Error:", error_message)

        if "429" in error_message:
            return """
            😊 Thank you for contacting our support team!

            Our AI assistant is currently busy.

            You can still get help with:

            📦 Order Verification
            💰 Refund Requests
            🔄 Product Replacement
            📋 Complaint Registration

            Please try again later.
            """

        else:
            return "Sorry! Our support assistant is temporarily unavailable. Please try again later."