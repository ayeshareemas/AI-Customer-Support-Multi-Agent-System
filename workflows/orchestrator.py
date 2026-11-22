from agents.complaint_agent import analyze_complaint
from agents.order_agent import lookup_order
from agents.policy_agent import check_policy
from agents.response_agent import generate_response


def run_workflow(
    complaint_text,
    customer_name,
    order_id,
    category_model,
    sentiment_model,
    priority_model
):

    # Agent 1: Analyse complaint
    analysis = analyze_complaint(
        complaint_text,
        category_model,
        sentiment_model,
        priority_model
    )

    # Agent 2: Verify order
    order = lookup_order(order_id) if order_id else None

    # Agent 3: Check policy
    policy = check_policy(
        analysis["category"],
        analysis["priority"]
    )

    # Agent 4: Generate response
    name = customer_name

    if order:
        name = order["customer_name"]

    response = generate_response(
        name,
        analysis["category"],
        analysis["sentiment"],
        analysis["priority"],
        policy["resolution"]
    )

    return {
        "analysis": analysis,
        "order": order,
        "policy": policy,
        "response": response
    }