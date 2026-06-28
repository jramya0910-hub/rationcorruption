from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import numpy as np

# Training corpus (keyword-based synthetic dataset)
_TRAINING_DATA = [
    # UNDERWEIGHT
    ("weight was less than stated", "UNDERWEIGHT"),
    ("received less rice than entitled", "UNDERWEIGHT"),
    ("only gave half the quantity", "UNDERWEIGHT"),
    ("short weight detected on scale", "UNDERWEIGHT"),
    ("missing kilograms from my allocation", "UNDERWEIGHT"),
    ("quantity given was much less", "UNDERWEIGHT"),
    ("weighed the bag and found it short", "UNDERWEIGHT"),
    ("less than the permitted quantity", "UNDERWEIGHT"),
    ("cheated on the weight of wheat", "UNDERWEIGHT"),
    ("only 2 kg instead of 5 kg", "UNDERWEIGHT"),
    # POOR_QUALITY
    ("rice had stones and insects", "POOR_QUALITY"),
    ("wheat quality was very bad smells rotten", "POOR_QUALITY"),
    ("sugar was damp and lumpy", "POOR_QUALITY"),
    ("oil was dirty and smelled strange", "POOR_QUALITY"),
    ("grains were mixed with sand", "POOR_QUALITY"),
    ("food items were expired", "POOR_QUALITY"),
    ("received damaged and mouldy stock", "POOR_QUALITY"),
    ("poor quality impure adulterated grain", "POOR_QUALITY"),
    ("rice full of pebbles", "POOR_QUALITY"),
    ("substandard ration supplied", "POOR_QUALITY"),
    # OVERCHARGING
    ("demanded extra money above government price", "OVERCHARGING"),
    ("charged more than fixed rate", "OVERCHARGING"),
    ("asked for bribe to give ration", "OVERCHARGING"),
    ("black market rate charged for wheat", "OVERCHARGING"),
    ("shopkeeper asked for additional payment", "OVERCHARGING"),
    ("unofficial surcharge collected", "OVERCHARGING"),
    ("extra rupees demanded illegally", "OVERCHARGING"),
    ("price was higher than official rate", "OVERCHARGING"),
    ("corruption overcharge bribe payment demanded", "OVERCHARGING"),
    ("had to pay more than maximum retail price", "OVERCHARGING"),
    # NOT_AVAILABLE
    ("shop was closed during distribution days", "NOT_AVAILABLE"),
    ("stock not available at all", "NOT_AVAILABLE"),
    ("no rice wheat available in shop", "NOT_AVAILABLE"),
    ("shop did not open for the month", "NOT_AVAILABLE"),
    ("ration not distributed this month", "NOT_AVAILABLE"),
    ("could not get grain shop closed", "NOT_AVAILABLE"),
    ("no stock found at shop", "NOT_AVAILABLE"),
    ("distribution window passed without goods", "NOT_AVAILABLE"),
    ("items out of stock", "NOT_AVAILABLE"),
    ("shop refused to distribute", "NOT_AVAILABLE"),
]

_pipeline: Pipeline = None


def _get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        texts  = [t for t, _ in _TRAINING_DATA]
        labels = [l for _, l in _TRAINING_DATA]
        _pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
            ("clf",   MultinomialNB(alpha=0.5)),
        ])
        _pipeline.fit(texts, labels)
    return _pipeline


def categorize_complaint(description: str) -> str:
    """
    Returns one of: UNDERWEIGHT | POOR_QUALITY | OVERCHARGING | NOT_AVAILABLE | OTHER
    """
    if not description or not description.strip():
        return "OTHER"
    try:
        pipeline = _get_pipeline()
        pred = pipeline.predict([description.lower()])[0]
        proba = pipeline.predict_proba([description.lower()]).max()
        if proba < 0.35:
            return "OTHER"
        return pred
    except Exception:
        return "OTHER"
