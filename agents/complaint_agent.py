# Complaint Analysis Agent

def analyze_complaint(text, category_model, sentiment_model, priority_model):

    # Complaint Category Prediction
    category = category_model.predict([text])[0]

    # Sentiment Analysis
    sentiment = sentiment_model.predict([text])[0]

    # Priority Prediction
    priority = priority_model.predict([text])[0]

    # Store analysis results
    result = {
        "category": category,
        "sentiment": sentiment,
        "priority": priority
    }

    return result