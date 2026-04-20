# Task 10 - Restaurant Information Chatbot

This project implements a Flask-based chatbot web app for restaurant information.
It uses:

- Word embeddings with `Word2Vec` (Gensim)
- ANN intent classifier with `TensorFlow/Keras`
- Dynamic frontend with HTML, CSS, and JavaScript (`fetch`)

## Project Structure

```text
task 10/
├─ app.py
├─ train_model.py
├─ requirements.txt
├─ data/
│  └─ intents.json
├─ model/                   # created after training
├─ templates/
│  └─ index.html
└─ static/
   ├─ style.css
   └─ script.js
```

## Setup

1. Open terminal in this folder:

   ```bash
   cd "C:\Users\mahad aziz\Desktop\ai lab 4a\task 10"
   ```

2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Train the chatbot model:

   ```bash
   python train_model.py
   ```

4. Start Flask app:

   ```bash
   python app.py
   ```

5. Open in browser:
   - <http://127.0.0.1:5000>

## Notes

- If you edit `data/intents.json`, run `python train_model.py` again.
- Confidence threshold is set in `model/metadata.json` after training.
