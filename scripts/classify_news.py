"""
Classifica le notizie per tematica usando keyword matching.

Input: src/data/auto/notizie.json
Output: src/data/auto/notizie-per-tema.json
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR, TEMA_KEYWORDS


def classify(notizia):
    """Restituisce la lista di temi associati a una notizia."""
    testo = (notizia.get('titolo', '') + ' ' + notizia.get('descrizione', '')).lower()
    temi = []
    for tema, keywords in TEMA_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in testo:
                temi.append(tema)
                break
    return temi


def main():
    print("=== Classificazione Notizie per Tema ===")

    notizie_path = os.path.join(DATA_DIR, 'notizie.json')
    if not os.path.exists(notizie_path):
        print("Nessun file notizie.json trovato. Esegui prima fetch_rss.py")
        return

    with open(notizie_path, 'r', encoding='utf-8') as f:
        notizie = json.load(f)

    # Classifica
    per_tema = {}
    non_classificate = 0

    for notizia in notizie:
        temi = classify(notizia)
        if not temi:
            non_classificate += 1
        for tema in temi:
            if tema not in per_tema:
                per_tema[tema] = []
            per_tema[tema].append({
                'id': notizia['id'],
                'titolo': notizia['titolo'],
                'link': notizia['link'],
                'data': notizia['data'],
                'fonte': notizia['fonte'],
                'fonte_id': notizia['fonte_id']
            })

    # Ordina notizie per data in ogni tema
    for tema in per_tema:
        per_tema[tema].sort(key=lambda x: x.get('data', ''), reverse=True)
        # Max 20 notizie per tema
        per_tema[tema] = per_tema[tema][:20]

    # Salva
    output_path = os.path.join(DATA_DIR, 'notizie-per-tema.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(per_tema, f, ensure_ascii=False, indent=2)

    # Report
    print(f"\nClassificazione completata:")
    for tema, news in sorted(per_tema.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {tema}: {len(news)} notizie")
    print(f"  Non classificate: {non_classificate}")
    print(f"\nSalvato in {output_path}")


if __name__ == '__main__':
    main()
