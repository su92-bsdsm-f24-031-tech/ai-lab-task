import json
import os
import pickle
import re

import numpy as np
from gensim.models import Word2Vec
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import to_categorical


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "intents.json")
MODEL_DIR = os.path.join(BASE_DIR, "model")
W2V_PATH = os.path.join(MODEL_DIR, "w2v.model")
LABEL_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
INTENT_MODEL_PATH = os.path.join(MODEL_DIR, "intent_model.keras")
META_PATH = os.path.join(MODEL_DIR, "metadata.json")


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def sentence_to_vector(tokens, w2v_model, vector_size: int) -> np.ndarray:
    vectors = [w2v_model.wv[word] for word in tokens if word in w2v_model.wv]
    if not vectors:
        return np.zeros(vector_size, dtype=np.float32)
    return np.mean(vectors, axis=0).astype(np.float32)


def load_intents(path: str):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["intents"]


def main() -> None:
    intents = load_intents(DATA_PATH)
    texts = []
    labels = []
    responses_map = {}

    for intent in intents:
        tag = intent["tag"]
        responses_map[tag] = intent["responses"]
        for pattern in intent["patterns"]:
            cleaned = clean_text(pattern)
            texts.append(cleaned.split())
            labels.append(tag)

    vector_size = 100
    w2v_model = Word2Vec(
        sentences=texts,
        vector_size=vector_size,
        window=5,
        min_count=1,
        workers=1,
        epochs=200,
    )

    features = np.array(
        [sentence_to_vector(tokens, w2v_model, vector_size) for tokens in texts],
        dtype=np.float32,
    )

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(labels)
    y_one_hot = to_categorical(y_encoded)

    model = Sequential(
        [
            Input(shape=(vector_size,)),
            Dense(128, activation="relu"),
            Dropout(0.25),
            Dense(64, activation="relu"),
            Dropout(0.2),
            Dense(len(label_encoder.classes_), activation="softmax"),
        ]
    )

    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    model.fit(features, y_one_hot, epochs=250, batch_size=8, verbose=0)

    os.makedirs(MODEL_DIR, exist_ok=True)
    w2v_model.save(W2V_PATH)
    model.save(INTENT_MODEL_PATH)
    with open(LABEL_PATH, "wb") as file:
        pickle.dump(label_encoder, file)

    metadata = {
        "vector_size": vector_size,
        "confidence_threshold": 0.45,
        "responses_map": responses_map,
        "fallback_tag": "fallback",
    }
    with open(META_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    print("Training complete.")
    print(f"Saved Word2Vec model: {W2V_PATH}")
    print(f"Saved ANN model: {INTENT_MODEL_PATH}")
    print(f"Saved LabelEncoder: {LABEL_PATH}")
    print(f"Saved metadata: {META_PATH}")


if __name__ == "__main__":
    main()
