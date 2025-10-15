# gmail_api.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import base64
import re

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"

def get_gmail_service(credentials: Credentials):
    return build('gmail', 'v1', credentials=credentials, cache_discovery=False)

def _get_plain_text_from_part(part):
    data = part.get('body', {}).get('data')
    if not data:
        return ''
    try:
        text = base64.urlsafe_b64decode(data).decode('utf-8')
    except Exception:
        text = base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='ignore')
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def fetch_message_by_id(service, user_id, msg_id):
    msg = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
    headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
    subject = headers.get('Subject', '')
    sender = headers.get('From', '')
    date = headers.get('Date', '')
    parts = []
    payload = msg.get('payload', {})
    if payload.get('parts'):
        for p in payload['parts']:
            mime = p.get('mimeType','')
            if mime.startswith('text/'):
                parts.append(_get_plain_text_from_part(p))
            elif p.get('parts'):
                for sub in p['parts']:
                    if sub.get('mimeType','').startswith('text/'):
                        parts.append(_get_plain_text_from_part(sub))
    else:
        parts.append(_get_plain_text_from_part(payload))
    body = ' '.join(parts)
    body = re.sub(r'\s+', ' ', body).strip()
    snippet = msg.get('snippet', '')
    return {
        'id': msg_id,
        'subject': subject,
        'from': sender,
        'date': date,
        'body': body if body else snippet
    }

def list_message_ids(service, user_id='me', max_results=50):
    res = service.users().messages().list(userId=user_id, labelIds=['INBOX'], maxResults=max_results).execute()
    messages = res.get('messages', [])
    return [m['id'] for m in messages]

