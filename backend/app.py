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

# Get environment variables with proper defaults
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://email-fraud-detector.netlify.app')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', f'{FRONTEND_URL}/dashboard/oauth2callback')
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'change_me')

# Configure CORS with the frontend URL
CORS(app, 
     supports_credentials=True, 
     origins=[FRONTEND_URL], 
     allow_credentials=True)

app.secret_key = FLASK_SECRET_KEY

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

model = EmailSpamModel()

def make_flow(state=None):
    return Flow.from_client_config(
        {
          "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI]
          }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

@app.route('/auth')
def auth():
    flow = make_flow()
    authorization_url, state = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return jsonify({'authorization_url': authorization_url})

@app.route('/oauth2callback/complete', methods=['POST'])
def oauth2callback_complete():
    try:
        data = request.get_json(silent=True) or {}
        auth_response_url = data.get('authorization_response')
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'No authorization code received'}), 400
            
        state = session.get('state')
        flow = make_flow(state=state)
        
        try:
            flow.fetch_token(code=code)
        except Exception as e:
            return jsonify({'error': f'Failed to fetch token: {str(e)}'}), 400
            
        creds = flow.credentials
        session['credentials'] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/session')
def check_session():
    if 'credentials' in session:
        return jsonify({'status': 'authenticated'})
    return jsonify({'status': 'unauthenticated'}), 401

@app.route('/api/scan', methods=['POST'])
def scan():
    if 'credentials' not in session:
        return jsonify({'error':'not_authenticated'}), 401
        
    try:
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
                heuristic_results.append({
                    'label': label, 
                    'score': float(min(score / 2.0, 1.0))
                })
            for e, r in zip(emails, heuristic_results):
                e['prediction'] = r
            return jsonify({
                'emails': emails, 
                'model': 'heuristic'
            })
            
        # Use trained model
        results = model.predict_many(emails)
        for e, r in zip(emails, results):
            e['prediction'] = r
        return jsonify({
            'emails': emails, 
            'model': 'ml'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout')
def logout():
    session.pop('credentials', None)
    return jsonify({'status': 'logged_out'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '10000'))
    app.run(host='0.0.0.0', port=port)