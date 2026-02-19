"""
Genera statistiche aggregate e timestamp aggiornamento.

Input: src/data/auto/notizie.json, notizie-per-tema.json
Output: src/data/auto/stats.json, last-update.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR


def main():
    print("=== Generazione Statistiche ===")

    # Carica notizie
    notizie_path = os.path.join(DATA_DIR, 'notizie.json')
    notizie = []
    if os.path.exists(notizie_path):
        with open(notizie_path, 'r', encoding='utf-8') as f:
            notizie = json.load(f)

    # Carica notizie per tema
    per_tema_path = os.path.join(DATA_DIR, 'notizie-per-tema.json')
    per_tema = {}
    if os.path.exists(per_tema_path):
        with open(per_tema_path, 'r', encoding='utf-8') as f:
            per_tema = json.load(f)

    # Conteggio notizie per fonte
    per_fonte = Counter(n.get('fonte_id', 'unknown') for n in notizie)

    # Temi piu attivi
    temi_attivi = sorted(
        [(tema, len(news)) for tema, news in per_tema.items()],
        key=lambda x: x[1],
        reverse=True
    )[:10]

    stats = {
        'totale_notizie': len(notizie),
        'notizie_per_fonte': dict(per_fonte),
        'temi_attivi': [{'tema': t, 'conteggio': c} for t, c in temi_attivi],
        'totale_temi_con_notizie': len(per_tema),
    }

    # Salva stats
    stats_path = os.path.join(DATA_DIR, 'stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Salva timestamp ultimo aggiornamento
    now = datetime.now(timezone.utc)
    last_update = {
        'timestamp': now.isoformat(),
        'timestamp_it': now.strftime('%d/%m/%Y ore %H:%M'),
        'date': now.strftime('%Y-%m-%d')
    }

    update_path = os.path.join(DATA_DIR, 'last-update.json')
    with open(update_path, 'w', encoding='utf-8') as f:
        json.dump(last_update, f, ensure_ascii=False, indent=2)

    print(f"  Notizie totali: {stats['totale_notizie']}")
    print(f"  Temi con notizie: {stats['totale_temi_con_notizie']}")
    print(f"  Aggiornamento: {last_update['timestamp_it']}")


if __name__ == '__main__':
    main()
