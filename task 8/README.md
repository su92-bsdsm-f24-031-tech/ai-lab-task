# Task 9 - NLP Sentiment Analysis

This folder contains starter code for a Natural Language Processing (NLP) subtask:
sentiment analysis (binary classification: positive vs negative).

## Files

- `sentiment_task.py` - end-to-end training and evaluation script
- `requirements.txt` - Python dependencies
- `sample_reviews.csv` - tiny sample dataset to test the pipeline quickly

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the script:

   ```bash
   python sentiment_task.py
   ```

## Expected Output

- Accuracy score
- Classification report
- Confusion matrix (console text)
- Predictions on custom example sentences

## Upgrade Ideas

- Replace `sample_reviews.csv` with a larger dataset (IMDb or Twitter).
- Add lemmatization and hyperparameter tuning.
- Save best model with `pickle` for reuse.
