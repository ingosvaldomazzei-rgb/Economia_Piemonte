"""
Scraping atti dal Consiglio Regionale del Piemonte.
Recupera interrogazioni, mozioni, OdG e proposte di legge recenti.
"""

import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import DATA_DIR

CONSIGLIO_BASE = 'https://www.cr.piemonte.it'

SEZIONI_ATTI = [
    {
        'tipo': 'interrogazioni',
        'url': f'{CONSIGLIO_BASE}/cms/atti/interrogazioni.html',
        'label': 'Interrogazioni'
    },
    {
        'tipo': 'mozioni',
        'url': f'{CONSIGLIO_BASE}/cms/atti/mozioni.html',
        'label': 'Mozioni'
    },
    {
        'tipo': 'ordini-del-giorno',
        'url': f'{CONSIGLIO_BASE}/cms/atti/ordini-del-giorno.html',
        'label': 'Ordini del Giorno'
    }
]

def scrape_atti():
    """Scrape degli atti consiliari più recenti."""
    tutti_atti = []
    headers = {
        'User-Agent': 'OsservatorioPiemonte/1.0 (monitoraggio civico; economia-piemonte.pages.dev)'
    }

    for sezione in SEZIONI_ATTI:
        try:
            print(f"  Fetching {sezione['label']}...")
            resp = requests.get(sezione['url'], headers=headers, timeout=20)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'lxml')
            # Il sito del CR usa tabelle o liste per gli atti
            righe = soup.select('table.atti tr, .elenco-atti li, .item-atto, article.atto')

            for riga in righe[:20]:
                link_el = riga.find('a')
                if not link_el:
                    continue
                titolo = link_el.get_text(strip=True)
                href = link_el.get('href', '')
                if href and not href.startswith('http'):
                    href = CONSIGLIO_BASE + href

                # Cerca data nel testo
                data_el = riga.find(class_='data') or riga.find('time') or riga.find('td')
                data_str = data_el.get_text(strip=True) if data_el else ''

                if titolo and len(titolo) > 5:
                    tutti_atti.append({
                        'tipo': sezione['tipo'],
                        'tipo_label': sezione['label'],
                        'titolo': titolo[:300],
                        'url': href,
                        'data': data_str[:20],
                        'fonte': 'Consiglio Regionale'
                    })
        except Exception as e:
            print(f"  Errore {sezione['label']}: {e}")

    output = {
        'ultimo_aggiornamento': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'atti': tutti_atti,
        'totale': len(tutti_atti)
    }

    out_path = os.path.join(DATA_DIR, 'atti-consiglio.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  Atti recuperati: {len(tutti_atti)}")
    return output

if __name__ == '__main__':
    print("=== Scraping Atti Consiglio Regionale ===")
    scrape_atti()
