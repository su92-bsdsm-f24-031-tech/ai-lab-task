import json
import os
import re

import faiss
import numpy as np
from flask import Flask, jsonify, render_template, request
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
FAISS_INDEX_PATH = os.path.join(MODEL_DIR, "qna.index")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.json")
SIMILARITY_THRESHOLD = 0.35
TOP_K = 3

app = Flask(__name__)

encoder = None
index = None
records = []
load_error = None


def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def load_assets() -> None:
    global encoder, index, records

    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError("qna.index not found. Run build_faiss_index.py first.")
    if not os.path.exists(METADATA_PATH):
        raise FileNotFoundError("metadata.json not found. Run build_faiss_index.py first.")

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    records = metadata.get("records", [])
    if not records:
        raise ValueError("No records found in metadata.json.")

    encoder = SentenceTransformer(metadata["embedding_model"])
    index = faiss.read_index(FAISS_INDEX_PATH)


def search_qna(query: str, top_k: int = TOP_K) -> list[dict]:
    query_clean = clean_text(query)
    query_vector = encoder.encode([query_clean], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vector)

    scores, ids = index.search(query_vector, top_k)

    matches = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0 or idx >= len(records):
            continue
        matches.append(
            {
                "question": records[idx]["question"],
                "answer": records[idx]["answer"],
                "score": round(float(score), 3),
            }
        )

    return matches


try:
    load_assets()
except Exception as error:  # pragma: no cover
    load_error = str(error)


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
                    "reply": "Model assets are missing. Please run preprocess_data.py and build_faiss_index.py.",
                    "detail": load_error,
                }
            ),
            500,
        )

    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"ok": False, "reply": "Please enter a question."}), 400

    matches = search_qna(message, top_k=TOP_K)
    if not matches:
        return jsonify({"ok": True, "reply": "No close match found.", "matches": []})

    best_match = matches[0]
    if best_match["score"] < SIMILARITY_THRESHOLD:
        reply = "I could not find a confident match. Please rephrase your question."
    else:
        reply = best_match["answer"]

    return jsonify(
        {
            "ok": True,
            "reply": reply,
            "best_match_question": best_match["question"],
            "best_match_score": best_match["score"],
            "matches": matches,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
