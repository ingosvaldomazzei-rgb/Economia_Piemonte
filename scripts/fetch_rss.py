"""
Scarica e unifica le notizie dai 3 feed RSS istituzionali.

Output: src/data/auto/notizie.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import md5
from html import unescape

import requests
from lxml import etree

# Aggiungi la directory scripts al path
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR, RSS_FEEDS

MAX_NOTIZIE = 200
REQUEST_TIMEOUT = 30

# Namespace comuni nei feed RSS
NAMESPACES = {
    'dc': 'http://purl.org/dc/elements/1.1/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'atom': 'http://www.w3.org/2005/Atom',
}


def strip_html(text):
    """Rimuovi tag HTML e normalizza spazi."""
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', unescape(text))
    return ' '.join(text.split()).strip()


def get_element_text(item, tag):
    """Estrai testo da un elemento XML, gestendo HTML inline nei tag."""
    el = item.find(tag)
    if el is None:
        return ''
    # Prendi tutto il contenuto testuale (incluso testo dentro tag figli)
    raw = etree.tostring(el, method='text', encoding='unicode')
    if raw and raw.strip():
        return raw.strip()
    # Fallback: serializza il contenuto come HTML e poi strippalo
    inner = etree.tostring(el, encoding='unicode')
    return strip_html(inner)


def parse_date(item):
    """Estrai e parsa la data di pubblicazione da un item RSS."""
    for tag in ['pubDate', 'dc:date', '{http://purl.org/dc/elements/1.1/}date']:
        el = item.find(tag, NAMESPACES) if ':' in tag else item.find(tag)
        if el is not None and el.text:
            try:
                return parsedate_to_datetime(el.text.strip()).isoformat()
            except Exception:
                try:
                    return datetime.fromisoformat(el.text.strip()).isoformat()
                except Exception:
                    pass
    return datetime.now(timezone.utc).isoformat()


def fetch_feed(feed_config):
    """Scarica e parsa un singolo feed RSS."""
    notizie = []
    try:
        resp = requests.get(feed_config['url'], timeout=REQUEST_TIMEOUT, headers={
            'User-Agent': 'OsservatorioPiemonte/1.0 (monitoraggio politico)'
        })
        resp.raise_for_status()

        root = etree.fromstring(resp.content)

        # Trova tutti gli <item> (RSS) o <entry> (Atom)
        items = root.findall('.//item')
        if not items:
            items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

        for item in items:
            # Titolo: estrai testo pulito anche se contiene HTML
            titolo = strip_html(get_element_text(item, 'title')) or 'Senza titolo'

            # Link
            link_el = item.find('link')
            link = ''
            if link_el is not None:
                link = (link_el.text or link_el.get('href', '')).strip()

            # Descrizione
            desc_text = get_element_text(item, 'description')
            descrizione = strip_html(desc_text)[:500]

            # Data
            data = parse_date(item)

            # ID univoco basato su link
            notizia_id = md5(link.encode()).hexdigest()[:12]

            notizie.append({
                'id': notizia_id,
                'titolo': titolo,
                'link': link,
                'descrizione': descrizione,
                'data': data,
                'fonte': feed_config['nome'],
                'fonte_id': feed_config['id'],
                'colore': feed_config['colore']
            })

        print(f"  {feed_config['nome']}: {len(notizie)} notizie")

    except Exception as e:
        print(f"  ERRORE {feed_config['nome']}: {e}")

    return notizie


def main():
    print("=== Fetch RSS Feeds ===")

    # Crea directory output se non esiste
    os.makedirs(DATA_DIR, exist_ok=True)

    # Carica notizie esistenti per deduplicazione
    notizie_path = os.path.join(DATA_DIR, 'notizie.json')
    existing = {}
    if os.path.exists(notizie_path):
        with open(notizie_path, 'r', encoding='utf-8') as f:
            for n in json.load(f):
                existing[n['id']] = n

    # Scarica da tutti i feed
    nuove = []
    for feed_config in RSS_FEEDS:
        nuove.extend(fetch_feed(feed_config))

    # Merge con esistenti (nuove sovrascrivono)
    for n in nuove:
        existing[n['id']] = n

    # Ordina per data (piu recenti prima) e taglia a MAX_NOTIZIE
    tutte = sorted(existing.values(), key=lambda x: x.get('data', ''), reverse=True)
    tutte = tutte[:MAX_NOTIZIE]

    # Salva
    with open(notizie_path, 'w', encoding='utf-8') as f:
        json.dump(tutte, f, ensure_ascii=False, indent=2)

    print(f"\nTotale: {len(tutte)} notizie salvate in {notizie_path}")


if __name__ == '__main__':
    main()
