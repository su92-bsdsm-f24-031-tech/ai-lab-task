import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed_qna.json")
MODEL_DIR = os.path.join(BASE_DIR, "model")
FAISS_INDEX_PATH = os.path.join(MODEL_DIR, "qna.index")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.json")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main() -> None:
    if not os.path.exists(PROCESSED_DATA_PATH):
        raise FileNotFoundError(
            "processed_qna.json not found. Run preprocess_data.py first."
        )

    with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as file:
        records = json.load(file)

    if not records:
        raise ValueError("No records found in processed_qna.json.")

    texts = [item["combined_text"] for item in records]

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = model.encode(texts, convert_to_numpy=True).astype("float32")

    # Normalize vectors and use inner product to approximate cosine similarity.
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    os.makedirs(MODEL_DIR, exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)

    metadata = {
        "embedding_model": EMBEDDING_MODEL_NAME,
        "total_records": len(records),
        "records": [
            {"question": item["question"], "answer": item["answer"]} for item in records
        ],
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    print(f"Saved FAISS index: {FAISS_INDEX_PATH}")
    print(f"Saved metadata: {METADATA_PATH}")
    print(f"Indexed records: {len(records)}")


if __name__ == "__main__":
    main()
