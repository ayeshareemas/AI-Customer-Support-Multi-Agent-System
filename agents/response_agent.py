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


def generate_response(
    complaint,
    category=None,
    sentiment=None,
    priority=None,
    customer_name=None,
    **kwargs
):

    system_prompt = """
    You are a friendly and professional AI Customer Support Response Agent.

    Your job is to generate helpful customer support responses
    based on the customer's complaint.

    Follow these rules:

    1. Be polite, empathetic, and professional.
    2. Acknowledge the customer's problem.
    3. Use simple and clear English.
    4. Provide helpful next steps.
    5. Never invent order details.
    6. Never claim a refund or replacement is approved
       unless the system confirms it.
    7. If information is missing, ask the customer politely.
    8. Keep responses concise and customer-friendly.
    9. Consider the complaint category, sentiment,
       and priority when generating the response.
    """

    user_prompt = f"""
    Customer Complaint: {complaint}

    Complaint Category: {category or 'Not specified'}

    Customer Sentiment: {sentiment or 'Not specified'}

    Complaint Priority: {priority or 'Not specified'}

    Customer Name: {customer_name or 'Not specified'}

    Generate an appropriate customer support response.
    """

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.5
        )

        return response.choices[0].message.content

    except Exception as e:

        print("Groq Response Agent Error:", str(e))

        return (
            "We are sorry to hear about your issue. "
            "Our customer support team will review your complaint "
            "and help you with the next steps. Thank you for your patience."
        )