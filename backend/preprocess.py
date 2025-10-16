# preprocess.py
import re
from bs4 import BeautifulSoup

PHISHING_KEYWORDS = [
    'verify', 'account', 'password', 'login', 'urgent', 'click', 'bank', 'confirm', 'suspend',
    'update', 'security', 'credit card', 'card', 'ssn','invoice','payment','wire'
]

def html_to_text(html):
    soup = BeautifulSoup(html or '', 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def clean_text(text):
    text = html_to_text(text)
    text = text.lower()
    text = re.sub(r'http\S+', ' ', text)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_features(email_record):
    original_body = email_record.get('body','') or ''
    text = clean_text(original_body + ' ' + (email_record.get('subject','') or ''))
    # Simple tokenization & stopword filtering (no external models)
    SIMPLE_STOPWORDS = set([
        'the','a','an','and','or','but','if','to','of','in','on','for','with','at','by','from','as','is','are','was','were','be','been','it','this','that','these','those','you','your','yours','we','us','our','they','their','them','he','she','his','her','its','not','no','do','does','did','can','could','should','would','will','just','about','into','out','up','down','over','under'
    ])
    tokens = [t for t in re.findall(r'[a-z]{3,}', text) if t not in SIMPLE_STOPWORDS]
    token_text = ' '.join(tokens)
    links = re.findall(r'https?://[^\s>\)\"]+', original_body)
    link_count = len(links)
    cap_count = sum(1 for c in (email_record.get('body','') or '') if c.isupper())
    body_len = max(len(email_record.get('body','') or ''),1)
    capital_ratio = cap_count / body_len
    keyword_count = sum(1 for k in PHISHING_KEYWORDS if k in text)
    return {
        'text': token_text,
        'link_count': link_count,
        'capital_ratio': capital_ratio,
        'keyword_count': keyword_count,
        'links': links
    }

