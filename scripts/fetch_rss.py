"""
Scarica e unifica le notizie dai 3 feed RSS istituzionali.

Output: src/data/auto/notizie.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from hashlib import md5

import atoma
import requests

# Aggiungi la directory scripts al path
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR, RSS_FEEDS

MAX_NOTIZIE = 100
REQUEST_TIMEOUT = 30


def fetch_feed(feed_config):
    """Scarica e parsa un singolo feed RSS."""
    notizie = []
    try:
        resp = requests.get(feed_config['url'], timeout=REQUEST_TIMEOUT, headers={
            'User-Agent': 'OsservatorioPiemonte/1.0 (monitoraggio politico)'
        })
        resp.raise_for_status()
        feed = atoma.parse_rss_bytes(resp.content)

        for item in feed.items or []:
            # Estrai data pubblicazione
            data = None
            if item.pub_date:
                data = item.pub_date.isoformat()
            else:
                data = datetime.now(timezone.utc).isoformat()

            # Pulisci descrizione (rimuovi tag HTML)
            descrizione = ''
            if item.description:
                from html import unescape
                import re
                descrizione = re.sub(r'<[^>]+>', '', unescape(item.description))
                descrizione = descrizione.strip()[:500]  # Max 500 caratteri

            titolo = item.title or 'Senza titolo'
            link = item.link or ''

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
