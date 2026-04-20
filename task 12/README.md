# Task 12 - QnA Bot (MiniLM + FAISS + Flask)

This task builds a retrieval-based Question Answering bot using the same pipeline requested in class:

1. Preprocess text-based QnA dataset
2. Generate embeddings using Hugging Face MiniLM
3. Store vectors in FAISS
4. Search by vector similarity
5. Display answers through Flask + HTML UI

## Project Structure

```text
task 12/
├─ app.py
├─ preprocess_data.py
├─ build_faiss_index.py
├─ requirements.txt
├─ README.md
├─ data/
│  ├─ raw_qna.json
│  └─ processed_qna.json      # generated after preprocessing
├─ model/
│  ├─ qna.index               # generated after indexing
│  └─ metadata.json           # generated after indexing
├─ templates/
│  └─ index.html
└─ static/
   ├─ style.css
   └─ script.js
```

## Setup

1. Open terminal in this folder:

```bash
cd "C:\Users\mahad aziz\Desktop\ai lab 4a\task 12"
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run Pipeline

1. Preprocess dataset:

```bash
python preprocess_data.py
```

2. Build MiniLM embeddings + FAISS index:

```bash
python build_faiss_index.py
```

3. Start Flask app:

```bash
python app.py
```

4. Open in browser:

- <http://127.0.0.1:5000>

## Notes

- Edit `data/raw_qna.json` to customize your topic data.
- Re-run preprocessing and indexing after changing the dataset.
- `SIMILARITY_THRESHOLD` can be tuned in `app.py` for stricter or softer matching.
