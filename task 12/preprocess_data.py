import json
import os
import re
from typing import Any


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw_qna.json")
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed_qna.json")


def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def preprocess_records(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    cleaned_records: list[dict[str, str]] = []
    seen_questions: set[str] = set()

    for item in records:
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not question or not answer:
            continue

        question_clean = clean_text(question)
        answer_clean = clean_text(answer)
        if not question_clean or question_clean in seen_questions:
            continue

        seen_questions.add(question_clean)
        cleaned_records.append(
            {
                "question": question,
                "answer": answer,
                "question_clean": question_clean,
                "answer_clean": answer_clean,
                "combined_text": f"question: {question_clean} answer: {answer_clean}",
            }
        )

    return cleaned_records


def main() -> None:
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as file:
        raw_records = json.load(file)

    processed_records = preprocess_records(raw_records)
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)

    with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(processed_records, file, indent=2, ensure_ascii=False)

    print(f"Loaded raw records: {len(raw_records)}")
    print(f"Processed records: {len(processed_records)}")
    print(f"Saved to: {PROCESSED_DATA_PATH}")


if __name__ == "__main__":
    main()
