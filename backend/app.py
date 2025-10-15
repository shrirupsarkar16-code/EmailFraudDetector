# app.py
import os
from flask import Flask, session, redirect, url_for, request, jsonify, send_from_directory
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from gmail_api import get_gmail_service, list_message_ids, fetch_message_by_id
from preprocess import extract_features
from model import EmailSpamModel
from flask_cors import CORS

load_dotenv()
app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
CORS(app, supports_credentials=True, origins=["https://email-scam-detector.netlify.app", "http://localhost:5173"], allow_credentials=True)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change_me')

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
# Use environment variable for redirect URI with appropriate fallback
OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', 'https://email-scam-detector-api.onrender.com/oauth2callback')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

model = EmailSpamModel()

def make_flow(state=None):
    return Flow.from_client_config(
        {
          "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
          }
        },
        scopes=SCOPES,
        redirect_uri=OAUTH_REDIRECT_URI
    )

@app.route('/auth')
def auth():
    flow = make_flow()
    authorization_url, state = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session.get('state', None)
    flow = make_flow(state=state)
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    return redirect('/')

# Alias path to match provided redirect URI
@app.route('/auth/gmail/callback')
def oauth2callback_alias():
    return oauth2callback()

@app.route('/api/scan', methods=['POST'])
def scan():
    if 'credentials' not in session:
        return jsonify({'error':'not_authenticated'}), 401
    creds = Credentials(**session['credentials'])
    if 'https://www.googleapis.com/auth/gmail.readonly' not in creds.scopes:
        return jsonify({'error':'required_scope_missing'}), 403
    service = get_gmail_service(creds)
    msg_ids = list_message_ids(service, max_results=30)
    emails = []
    for mid in msg_ids:
        e = fetch_message_by_id(service, 'me', mid)
        features = extract_features(e)
        emails.append({**e, **features})
    if not model.is_loaded():
        return jsonify({'error':'model_not_loaded', 'message':'Place a trained model at MODEL_PATH'}), 500
    results = model.predict_many(emails)
    for e, r in zip(emails, results):
        e['prediction'] = r
    return jsonify({'emails': emails})

@app.route('/api/logout')
def logout():
    session.pop('credentials', None)
    return jsonify({'ok': True})

@app.route('/')
def serve_frontend():
    # Serve built frontend if present
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)

