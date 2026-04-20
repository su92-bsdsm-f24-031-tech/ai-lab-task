import json
import os
import pickle
import random
import re

import numpy as np
from flask import Flask, jsonify, render_template, request
from gensim.models import Word2Vec
from tensorflow.keras.models import load_model


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
W2V_PATH = os.path.join(MODEL_DIR, "w2v.model")
LABEL_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
INTENT_MODEL_PATH = os.path.join(MODEL_DIR, "intent_model.keras")
META_PATH = os.path.join(MODEL_DIR, "metadata.json")

app = Flask(__name__)

w2v_model = None
intent_model = None
label_encoder = None
metadata = {}


def clean_text(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = " ".join(text.split())
    return text.split()


def sentence_to_vector(tokens: list[str], vector_size: int) -> np.ndarray:
    vectors = [w2v_model.wv[word] for word in tokens if word in w2v_model.wv]
    if not vectors:
        return np.zeros(vector_size, dtype=np.float32)
    return np.mean(vectors, axis=0).astype(np.float32)


def load_assets() -> str | None:
    global w2v_model, intent_model, label_encoder, metadata
    try:
        w2v_model = Word2Vec.load(W2V_PATH)
        intent_model = load_model(INTENT_MODEL_PATH)
        with open(LABEL_PATH, "rb") as file:
            label_encoder = pickle.load(file)
        with open(META_PATH, "r", encoding="utf-8") as file:
            metadata = json.load(file)
        return None
    except Exception as error:  # pragma: no cover
        return str(error)


load_error = load_assets()


def predict_intent(message: str):
    vector_size = int(metadata.get("vector_size", 100))
    threshold = float(metadata.get("confidence_threshold", 0.45))
    fallback_tag = metadata.get("fallback_tag", "fallback")
    responses_map = metadata.get("responses_map", {})

    tokens = clean_text(message)
    features = sentence_to_vector(tokens, vector_size).reshape(1, -1)
    probs = intent_model.predict(features, verbose=0)[0]
    best_idx = int(np.argmax(probs))
    confidence = float(probs[best_idx])
    predicted_tag = label_encoder.inverse_transform([best_idx])[0]

    if confidence < threshold:
        predicted_tag = fallback_tag

    responses = responses_map.get(predicted_tag, responses_map.get(fallback_tag, []))
    response_text = random.choice(responses) if responses else "Please ask another question."

    return predicted_tag, confidence, response_text


@app.route("/")
def home():
    return render_template("index.html", load_error=load_error)


@app.route("/chat", methods=["POST"])
def chat():
    if load_error is not None:
        return (
            jsonify(
                {
                    "ok": False,
                    "reply": "Model is not ready. Please run train_model.py first.",
                    "detail": load_error,
                }
            ),
            500,
        )

    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"ok": False, "reply": "Please enter a message."}), 400

    tag, confidence, reply = predict_intent(message)
    return jsonify(
        {
            "ok": True,
            "reply": reply,
            "intent": tag,
            "confidence": round(confidence, 3),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
