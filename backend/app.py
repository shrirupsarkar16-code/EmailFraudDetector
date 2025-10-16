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
# Allow HTTP OAuth locally for Google (only when redirecting to localhost)
if os.environ.get('OAUTH_REDIRECT_URI', '').startswith('http://localhost'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
CORS(app, supports_credentials=True, origins=["https://email-scam-detector.netlify.app", "http://localhost:5173", "http://localhost:3000"], allow_credentials=True)
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
    return redirect('/dashboard')

# Supports front-end redirect URI (e.g., http://localhost:3000/dashboard/oauth2callback)
# The frontend posts back the full URL it received from Google so we can finish the code exchange.
@app.route('/oauth2callback/complete', methods=['POST'])
def oauth2callback_complete():
    data = request.get_json(silent=True) or {}
    auth_response_url = data.get('authorization_response')
    if not auth_response_url:
        return jsonify({'error': 'missing_authorization_response'}), 400
    state = request.args.get('state') or session.get('state')
    flow = make_flow(state=state)
    flow.fetch_token(authorization_response=auth_response_url)
    creds = flow.credentials
    session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    return jsonify({'ok': True})

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
    msg_ids = list_message_ids(service, max_results=100)
    emails = []
    for mid in msg_ids:
        e = fetch_message_by_id(service, 'me', mid)
        features = extract_features(e)
        emails.append({**e, **features})
    # If ML model not available, fall back to simple heuristic classification
    if not model.is_loaded():
        heuristic_results = []
        for e in emails:
            score = 0.0
            score += 0.25 * min(5, e.get('keyword_count', 0))
            score += 0.5 * min(1.0, e.get('capital_ratio', 0.0) * 5)
            score += 0.25 * min(5, e.get('link_count', 0))
            label = 'spam' if score >= 1.0 else 'ham'
            heuristic_results.append({'label': label, 'score': float(min(score / 2.0, 1.0))})
        for e, r in zip(emails, heuristic_results):
            e['prediction'] = r
        return jsonify({'emails': emails, 'model': 'heuristic'})
    # Use trained model
    results = model.predict_many(emails)
    for e, r in zip(emails, results):
        e['prediction'] = r
    return jsonify({'emails': emails, 'model': 'ml'})

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
    app.run(debug=True, host='127.0.0.1', port=port)

