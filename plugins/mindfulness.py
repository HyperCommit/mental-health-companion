from transformers import pipeline

# Initialize Hugging Face sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def analyze_mindfulness_feedback(feedback: str):
    """Analyze user feedback using Hugging Face sentiment analysis model."""
    result = sentiment_analyzer(feedback)
    return result