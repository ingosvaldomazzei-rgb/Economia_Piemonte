"""
Fetch dati qualità aria da ARPA Piemonte REST API.
Salva i rilevamenti PM10/PM2.5 per le stazioni configurate.
"""

import json
import os
import requests
from datetime import datetime, timedelta
from config import DATA_DIR, ARPA_STAZIONI

ARPA_API = 'https://aria.ambiente.piemonte.it/ariaweb/ariaws/rest/getRilevamenti'

def fetch_air_quality():
    """Recupera gli ultimi rilevamenti di qualità dell'aria."""
    oggi = datetime.now()
    ieri = oggi - timedelta(days=1)
    date_str = ieri.strftime('%Y-%m-%d')

    risultati = []
    for stazione in ARPA_STAZIONI:
        for inquinante in ['PM10', 'PM2.5', 'NO2']:
            try:
                params = {
                    'codStazione': stazione['id'],
                    'inquinante': inquinante,
                    'dataInizio': date_str,
                    'dataFine': date_str
                }
                resp = requests.get(ARPA_API, params=params, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        valore = data[-1].get('valore') if isinstance(data, list) else data.get('valore')
                        risultati.append({
                            'stazione': stazione['nome'],
                            'stazione_id': stazione['id'],
                            'provincia': stazione['provincia'],
                            'inquinante': inquinante,
                            'valore': valore,
                            'unita': 'µg/m³',
                            'data': date_str,
                            'superamento': valore > 50 if inquinante == 'PM10' and valore else False
                        })
            except Exception as e:
                print(f"  Errore {stazione['nome']} {inquinante}: {e}")

    output = {
        'ultimo_aggiornamento': oggi.strftime('%Y-%m-%dT%H:%M:%S'),
        'data_rilevamento': date_str,
        'rilevamenti': risultati,
        'stazioni_monitorate': len(ARPA_STAZIONI)
    }

    out_path = os.path.join(DATA_DIR, 'aria.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  Rilevamenti salvati: {len(risultati)}")
    return output

if __name__ == '__main__':
    print("=== Fetch Qualità Aria ARPA ===")
    fetch_air_quality()
