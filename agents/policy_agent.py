def check_policy(category, priority):

    # Category-based Resolution Recommendations
    if category == "Damaged Product":
        resolution = (
            "Verify the damage report and review the submitted evidence. "
            "Offer a replacement or refund review based on company policy."
        )
        action = "Review damage evidence and process the appropriate resolution."

    elif category == "Delivery Delay":
        resolution = (
            "Check shipment tracking details, identify the cause of delay, "
            "and provide the customer with an updated delivery estimate."
        )
        action = "Contact the delivery team and provide a shipment update."

    elif category == "Wrong Product":
        resolution = (
            "Verify the ordered product against the delivered product. "
            "Arrange an exchange or return according to company policy."
        )
        action = "Verify the product mismatch and initiate exchange review."

    elif category == "Refund Request":
        resolution = (
            "Review the order details, payment status, and refund eligibility. "
            "If eligible, initiate the refund approval process."
        )
        action = "Forward the refund request for authorized approval."

    elif category == "Payment Issue":
        resolution = (
            "Verify the payment transaction, check for duplicate charges "
            "or failed payments, and review the billing records."
        )
        action = "Refer the transaction to billing support for verification."

    else:
        resolution = (
            "Review the complaint details, identify the customer's issue, "
            "and determine an appropriate solution."
        )
        action = "Forward the complaint to customer support for manual review."

    # Priority-based Escalation
    if priority == "High":
        action = (
            "URGENT: Escalate to human support immediately "
            "and prioritize complaint resolution. " + action
        )

    elif priority == "Medium":
        action = (
            "Schedule a timely follow-up and monitor complaint progress. "
            + action
        )

    else:
        action = (
            "Continue with the standard support process. " + action
        )

    return {
        "resolution": resolution,
        "action": action,
        "human_approval_required": category == "Refund Request"
    }