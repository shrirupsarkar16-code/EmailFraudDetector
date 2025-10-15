# model.py
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer

MODEL_PATH = os.environ.get('MODEL_PATH','./model.joblib')

class EmailSpamModel:
    def __init__(self):
        self.vectorizer = None
        self.clf = None
        if os.path.exists(MODEL_PATH):
            data = joblib.load(MODEL_PATH)
            self.vectorizer = data['vectorizer']
            self.clf = data['model']

    def is_loaded(self):
        return self.vectorizer is not None and self.clf is not None

    def predict_many(self, feature_dicts):
        if not self.is_loaded():
            raise RuntimeError('Model not loaded. Train model and place model.joblib at MODEL_PATH')
        texts = [f['text'] for f in feature_dicts]
        X_text = self.vectorizer.transform(texts)
        probs = self.clf.predict_proba(X_text)[:,1]
        preds = (probs >= 0.5).astype(int)
        results = []
        for p, prob in zip(preds, probs):
            results.append({'label': 'spam' if p==1 else 'ham', 'score': float(prob)})
        return results

