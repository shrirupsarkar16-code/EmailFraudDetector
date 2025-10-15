Backend README - steps to run

1. Create a virtualenv, install requirements:
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Download spaCy model:
   python -m spacy download en_core_web_sm

3. Create .env from .env.example and fill Google client id & secret.

4. Train model with scripts/train_model.py (see root scripts) or copy a pre-trained model to MODEL_PATH.

5. Run Flask:
   python app.py

6. Visit frontend at http://localhost:3000 (if frontend dev server) or http://localhost:5000 after building frontend.

