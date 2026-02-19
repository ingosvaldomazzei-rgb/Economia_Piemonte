"""
Fetch dati da portali Open Data: dati.piemonte.it e Open Data Torino.
Recupera metadati sui dataset disponibili e statistiche aggregate.
"""

import json
import os
import requests
from datetime import datetime
from config import DATA_DIR, DATI_PIEMONTE_API, TORINO_OPENDATA_BASE, TORINO_DATASETS

def fetch_dati_piemonte():
    """Recupera statistiche e dataset recenti da dati.piemonte.it."""
    risultati = {
        'datasets_recenti': [],
        'tags_principali': [],
        'totale_datasets': 0
    }

    try:
        # Dataset recenti
        resp = requests.get(
            f'{DATI_PIEMONTE_API}/3/action/recently_changed_packages_activity_list',
            params={'limit': 15},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('result'):
                for item in data['result'][:15]:
                    pkg = item.get('data', {}).get('package', {})
                    if pkg.get('title'):
                        risultati['datasets_recenti'].append({
                            'titolo': pkg['title'],
                            'nome': pkg.get('name', ''),
                            'organizzazione': pkg.get('organization', {}).get('title', ''),
                            'data_modifica': item.get('timestamp', '')[:10]
                        })
    except Exception as e:
        print(f"  Errore datasets recenti: {e}")

    try:
        # Conteggio totale
        resp = requests.get(
            f'{DATI_PIEMONTE_API}/3/action/package_search',
            params={'rows': 0},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                risultati['totale_datasets'] = data['result']['count']
    except Exception as e:
        print(f"  Errore conteggio: {e}")

    try:
        # Tag più usati
        resp = requests.get(
            f'{DATI_PIEMONTE_API}/3/action/tag_list',
            params={'all_fields': True},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                risultati['tags_principali'] = [
                    t['name'] for t in data['result'][:30]
                ] if isinstance(data['result'], list) and data['result'] and isinstance(data['result'][0], dict) else data['result'][:30]
    except Exception as e:
        print(f"  Errore tags: {e}")

    return risultati

def fetch_torino_opendata():
    """Recupera disponibilità dataset Open Data Torino."""
    disponibili = []
    anno = datetime.now().year

    for dataset in TORINO_DATASETS:
        url = f'{TORINO_OPENDATA_BASE}/{dataset}{anno}.csv'
        try:
            resp = requests.head(url, timeout=10)
            disponibili.append({
                'dataset': dataset,
                'anno': anno,
                'url': url,
                'disponibile': resp.status_code == 200,
                'dimensione': resp.headers.get('Content-Length', 'N/D')
            })
        except Exception as e:
            disponibili.append({
                'dataset': dataset,
                'anno': anno,
                'url': url,
                'disponibile': False,
                'errore': str(e)
            })

    return disponibili

def main():
    piemonte = fetch_dati_piemonte()
    torino = fetch_torino_opendata()

    output = {
        'ultimo_aggiornamento': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'dati_piemonte': piemonte,
        'opendata_torino': torino
    }

    out_path = os.path.join(DATA_DIR, 'opendata.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  Dataset Piemonte recenti: {len(piemonte['datasets_recenti'])}")
    print(f"  Totale dataset Piemonte: {piemonte['totale_datasets']}")
    print(f"  Dataset Torino verificati: {len(torino)}")

if __name__ == '__main__':
    print("=== Fetch Open Data ===")
    main()
