import re
import nltk
import pandas as pd
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB


nltk.download("stopwords", quiet=True)
STOPWORDS = set(stopwords.words("english"))


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    words = [word for word in text.split() if word not in STOPWORDS]
    return " ".join(words)


def main() -> None:
    df = pd.read_csv("sample_reviews.csv")
    if not {"text", "label"}.issubset(df.columns):
        raise ValueError("CSV must contain 'text' and 'label' columns.")

    df["clean_text"] = df["text"].astype(str).apply(clean_text)

    x_train, x_test, y_train, y_test = train_test_split(
        df["clean_text"],
        df["label"],
        test_size=0.25,
        random_state=42,
        stratify=df["label"],
    )

    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
    x_train_tfidf = vectorizer.fit_transform(x_train)
    x_test_tfidf = vectorizer.transform(x_test)

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "MultinomialNB": MultinomialNB(),
    }

    best_name = None
    best_accuracy = -1.0
    best_model = None

    for name, model in models.items():
        model.fit(x_train_tfidf, y_train)
        preds = model.predict(x_test_tfidf)
        acc = accuracy_score(y_test, preds)
        print(f"\n{name} Accuracy: {acc:.4f}")
        if acc > best_accuracy:
            best_accuracy = acc
            best_name = name
            best_model = model

    assert best_model is not None
    best_preds = best_model.predict(x_test_tfidf)
    print(f"\nBest Model: {best_name}")
    print("\nClassification Report:")
    print(classification_report(y_test, best_preds))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, best_preds))

    sample_texts = [
        "I really enjoyed this product. Excellent quality!",
        "Very disappointing experience, waste of money.",
        "It was okay, not great but not terrible.",
    ]
    cleaned_samples = [clean_text(text) for text in sample_texts]
    sample_vectors = vectorizer.transform(cleaned_samples)
    sample_preds = best_model.predict(sample_vectors)

    print("\nSample Predictions:")
    for text, pred in zip(sample_texts, sample_preds):
        print(f"- {text} -> {pred}")


if __name__ == "__main__":
    main()
