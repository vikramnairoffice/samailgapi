import json
import os
from pathlib import Path

_cache = {}
_content_dir = Path(__file__).parent

def _load_text_list(filename):
    if filename in _cache:
        return _cache[filename]

    with open(_content_dir / filename, 'r', encoding='utf-8') as f:
        data = [line.strip() for line in f if line.strip()]

    _cache[filename] = data
    return data

def _load_json(filename):
    if filename in _cache:
        return _cache[filename]

    with open(_content_dir / filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    _cache[filename] = data
    return data

def load_remote_logo_urls():
    return _load_text_list('invoice/remote_logo_urls.txt')

def load_product_bundles():
    return _load_json('invoice/product_bundles.json')

def load_secondary_suffixes():
    return _load_text_list('invoice/secondary_suffixes.txt')

def load_product_description_choices():
    return _load_text_list('invoice/product_description_choices.txt')

def load_notes_options():
    return _load_text_list('invoice/notes_options.txt')

def load_term_buckets():
    return _load_json('invoice/term_buckets.json')

def load_default_subjects():
    return _load_text_list('email/default_subjects.txt')

def load_default_gmass_recipients():
    return _load_text_list('email/default_gmass_recipients.txt')

def load_body_parts():
    parts = {}
    for i in range(1, 6):
        parts[f'part{i}'] = _load_text_list(f'email/body_parts/part{i}.txt')
    return parts

def load_bodyB():
    return _load_text_list('email/bodyB.txt')