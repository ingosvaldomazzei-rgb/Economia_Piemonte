"""
Scraping dati dal Consiglio Regionale del Piemonte:
  - Sedute del Consiglio (con sintesi PDF)
  - Interrogazioni e Interpellanze
  - Mozioni e Ordini del Giorno

Output: src/data/auto/consiglio.json
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from hashlib import md5

import requests
from bs4 import BeautifulSoup

try:
    import pypdfium2 as pdfium
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("  AVVISO: pypdfium2 non disponibile, i PDF non verranno estratti")

sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 2

HEADERS = {
    'User-Agent': 'OsservatorioPiemonte/1.0 (monitoraggio istituzionale; contatto: osservatorio@example.it)'
}

# --- URL di base ---
BASE_SEDUTE = 'https://www.cr.piemonte.it/seduteconsiglio/appl/search'
BASE_INTERFO = 'https://www.cr.piemonte.it/interfo'
BASE_MZODG = 'https://www.cr.piemonte.it/mzodgfo'

LEGISLATURA = 12  # XII Legislatura (corrente)


def fetch_sedute(max_pages=3):
    """Scarica le ultime sedute del Consiglio con link alle sintesi PDF."""
    sedute = []
    print("\n  --- Sedute del Consiglio ---")

    url = f'{BASE_SEDUTE}/index.php'
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Cerca tutti i link a sedute individuali
        links = soup.find_all('a', href=re.compile(r'seduta\.php'))
        if not links:
            # Fallback: cerca qualsiasi link con "seduta" nel testo
            links = soup.find_all('a', string=re.compile(r'Seduta', re.I))

        for link_el in links[:30]:
            href = link_el.get('href', '')
            text = link_el.get_text(strip=True)

            # Estrai numero seduta e data dal testo o dall'href
            num_match = re.search(r'numero_seduta=(\d+)', href) or re.search(r'n\.?\s*(\d+)', text)
            date_match = re.search(r'data_seduta=([\d-]+)', href)

            numero = num_match.group(1) if num_match else ''
            data_str = ''
            data_iso = ''

            if date_match:
                data_str = date_match.group(1)
                try:
                    dt = datetime.strptime(data_str, '%d-%m-%Y')
                    data_iso = dt.replace(tzinfo=timezone.utc).isoformat()
                    data_str = dt.strftime('%d/%m/%Y')
                except ValueError:
                    pass

            if not data_iso:
                # Prova a estrarre data dal testo "del DD/MM/YYYY" o "del DD-MM-YYYY"
                dm = re.search(r'del\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
                if dm:
                    try:
                        dt = datetime(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)),
                                      tzinfo=timezone.utc)
                        data_iso = dt.isoformat()
                        data_str = dt.strftime('%d/%m/%Y')
                    except ValueError:
                        pass

            if not data_iso:
                data_iso = datetime.now(timezone.utc).isoformat()

            if not numero:
                continue

            # Cerca il link alla sintesi PDF nel contesto circostante
            sintesi_url = ''
            parent = link_el.parent
            if parent:
                # Cerca tra i fratelli
                container = parent.parent if parent.parent else parent
                sintesi_links = container.find_all('a', href=re.compile(r'tipo=sintesi'))
                if sintesi_links:
                    sintesi_href = sintesi_links[0].get('href', '')
                    if sintesi_href.startswith('/'):
                        sintesi_url = 'https://www.cr.piemonte.it' + sintesi_href
                    elif sintesi_href.startswith('http'):
                        sintesi_url = sintesi_href
                    else:
                        sintesi_url = f'{BASE_SEDUTE}/{sintesi_href}'

            # Estrai testo dal PDF sintesi se disponibile
            sintesi_testo = ''
            if sintesi_url and HAS_PDF:
                sintesi_testo = _extract_pdf_text(sintesi_url)

            seduta_id = md5(f'seduta-{numero}'.encode()).hexdigest()[:12]
            sedute.append({
                'id': seduta_id,
                'tipo': 'seduta',
                'numero': numero,
                'titolo': f'Seduta n. {numero}' + (f' del {data_str}' if data_str else ''),
                'data': data_iso,
                'link': f'https://www.cr.piemonte.it/seduteconsiglio/appl/search/seduta.php?numero_seduta={numero}&data_seduta={data_str.replace("/", "-") if data_str else ""}',
                'sintesi_url': sintesi_url,
                'sintesi_testo': sintesi_testo,
            })

        print(f"    -> {len(sedute)} sedute trovate")

    except Exception as e:
        print(f"    ERRORE: {e}")

    time.sleep(DELAY_BETWEEN_REQUESTS)
    return sedute


def _extract_pdf_text(url, max_chars=5000):
    """Scarica un PDF e ne estrae il testo."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
        resp.raise_for_status()

        pdf = pdfium.PdfDocument(resp.content)
        text_parts = []
        for page in pdf:
            textpage = page.get_textpage()
            text_parts.append(textpage.get_text_range())
            textpage.close()
            page.close()
        pdf.close()

        full_text = '\n'.join(text_parts).strip()
        # Pulisci e tronca
        full_text = re.sub(r'\s+', ' ', full_text)
        return full_text[:max_chars]

    except Exception as e:
        print(f"      ERRORE estrazione PDF {url}: {e}")
        return ''


def fetch_interrogazioni(anno=2026, max_pages=3):
    """Scarica interrogazioni e interpellanze dall'ordine cronologico."""
    atti = []
    print(f"\n  --- Interrogazioni e Interpellanze ({anno}) ---")

    for page in range(1, max_pages + 1):
        url = f'{BASE_INTERFO}/legislatura/{LEGISLATURA}/anno/{anno}/pagina/{page}'
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Trova le righe della tabella
            rows = soup.find_all('tr')
            found = 0
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue

                first_cell = cells[0]
                second_cell = cells[1]

                # Estrai link e numero
                link_el = first_cell.find('a', href=re.compile(r'/interfo/legislatura/'))
                if not link_el:
                    continue

                href = link_el.get('href', '')
                link_text = link_el.get_text(strip=True)

                # Numero dall'href o dal testo
                num_match = re.search(r'/atto/(\d+)/', href)
                numero = num_match.group(1) if num_match else ''

                # Tipo (Interrogazione o Interpellanza)
                tipo_atto = 'interrogazione'
                if 'interpellanza' in link_text.lower():
                    tipo_atto = 'interpellanza'

                # Titolo dalla seconda cella
                titolo = second_cell.get_text(strip=True)

                # Data
                cell_text = first_cell.get_text()
                data_iso = ''
                date_match = re.search(r'del\s+(\d{1,2}/\d{1,2}/\d{4})', cell_text)
                if date_match:
                    try:
                        dt = datetime.strptime(date_match.group(1), '%d/%m/%Y')
                        data_iso = dt.replace(tzinfo=timezone.utc).isoformat()
                    except ValueError:
                        pass

                if not data_iso:
                    data_iso = datetime.now(timezone.utc).isoformat()

                # Status (es. "Ritirata", "Discussa")
                status = ''
                cell_full_text = first_cell.get_text()
                for s in ['Ritirata', 'Discussa', 'Non discussa', 'Decaduta', 'Trasformata']:
                    if s in cell_full_text:
                        status = s
                        break

                clean_href = re.sub(r';jsessionid=[^/]*', '', href)
                full_link = f'https://www.cr.piemonte.it{clean_href}' if clean_href.startswith('/') else clean_href

                atto_id = md5(f'interr-{numero}'.encode()).hexdigest()[:12]
                atti.append({
                    'id': atto_id,
                    'tipo': tipo_atto,
                    'numero': numero,
                    'titolo': titolo or f'{tipo_atto.capitalize()} n. {numero}',
                    'data': data_iso,
                    'link': full_link,
                    'stato': status,
                })
                found += 1

            print(f"    Pagina {page}: {found} atti")
            if found == 0:
                break

        except Exception as e:
            print(f"    ERRORE pagina {page}: {e}")
            break

        time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"    -> Totale: {len(atti)} interrogazioni/interpellanze")
    return atti


def fetch_mozioni(anno=2026, max_pages=3):
    """Scarica mozioni e ordini del giorno dall'ordine cronologico."""
    atti = []
    print(f"\n  --- Mozioni e Ordini del Giorno ({anno}) ---")

    for page in range(1, max_pages + 1):
        url = f'{BASE_MZODG}/legislatura/{LEGISLATURA}/anno/{anno}/pagina/{page}'
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            rows = soup.find_all('tr')
            found = 0
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue

                first_cell = cells[0]
                second_cell = cells[1]

                link_el = first_cell.find('a', href=re.compile(r'/mzodgfo/legislatura/'))
                if not link_el:
                    continue

                href = link_el.get('href', '')
                link_text = link_el.get_text(strip=True)

                num_match = re.search(r'/atto/(\d+)/', href)
                numero = num_match.group(1) if num_match else ''

                # Tipo
                tipo_atto = 'ordine_del_giorno'
                if 'mozione' in link_text.lower():
                    tipo_atto = 'mozione'

                titolo = second_cell.get_text(strip=True)

                # Data
                cell_text = first_cell.get_text()
                data_iso = ''
                date_match = re.search(r'del\s+([\d/-]+)', cell_text)
                if date_match:
                    date_str = date_match.group(1)
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y']:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            data_iso = dt.replace(tzinfo=timezone.utc).isoformat()
                            break
                        except ValueError:
                            continue

                if not data_iso:
                    data_iso = datetime.now(timezone.utc).isoformat()

                # Stato (approvato, non votato, ecc.)
                stato = ''
                for s in ['stato approvato', 'stato respinto', 'stato ritirato',
                          'Non è stato votato', 'non votato', 'Decadut']:
                    if s.lower() in cell_text.lower():
                        if 'approvato' in s.lower():
                            stato = 'Approvato'
                        elif 'respinto' in s.lower():
                            stato = 'Respinto'
                        elif 'ritirato' in s.lower():
                            stato = 'Ritirato'
                        elif 'votato' in s.lower():
                            stato = 'Non votato'
                        elif 'decadut' in s.lower():
                            stato = 'Decaduto'
                        break

                clean_href = re.sub(r';jsessionid=[^/]*', '', href)
                full_link = f'https://www.cr.piemonte.it{clean_href}' if clean_href.startswith('/') else clean_href

                atto_id = md5(f'mzodg-{numero}'.encode()).hexdigest()[:12]
                atti.append({
                    'id': atto_id,
                    'tipo': tipo_atto,
                    'numero': numero,
                    'titolo': titolo or f'{tipo_atto.replace("_", " ").capitalize()} n. {numero}',
                    'data': data_iso,
                    'link': full_link,
                    'stato': stato,
                })
                found += 1

            print(f"    Pagina {page}: {found} atti")
            if found == 0:
                break

        except Exception as e:
            print(f"    ERRORE pagina {page}: {e}")
            break

        time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"    -> Totale: {len(atti)} mozioni/ordini del giorno")
    return atti


def main():
    print("=== Fetch Dati Consiglio Regionale Piemonte ===")
    os.makedirs(DATA_DIR, exist_ok=True)

    # Carica dati esistenti
    output_path = os.path.join(DATA_DIR, 'consiglio.json')
    existing = {}
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for section in ['sedute', 'interrogazioni', 'mozioni']:
                for item in data.get(section, []):
                    existing[item['id']] = item

    # Fetch sedute
    sedute = fetch_sedute()

    # Fetch interrogazioni (anno corrente e precedente)
    interrogazioni = []
    for anno in [2026, 2025]:
        interrogazioni.extend(fetch_interrogazioni(anno=anno, max_pages=2))

    # Fetch mozioni (anno corrente e precedente)
    mozioni = []
    for anno in [2026, 2025]:
        mozioni.extend(fetch_mozioni(anno=anno, max_pages=2))

    # Merge con esistenti (nuovi sovrascrivono)
    for item in sedute + interrogazioni + mozioni:
        existing[item['id']] = item

    # Separa per tipo
    all_sedute = sorted(
        [v for v in existing.values() if v.get('tipo') == 'seduta'],
        key=lambda x: x.get('data', ''), reverse=True
    )
    all_interrogazioni = sorted(
        [v for v in existing.values() if v.get('tipo') in ('interrogazione', 'interpellanza')],
        key=lambda x: x.get('data', ''), reverse=True
    )
    all_mozioni = sorted(
        [v for v in existing.values() if v.get('tipo') in ('mozione', 'ordine_del_giorno')],
        key=lambda x: x.get('data', ''), reverse=True
    )

    output = {
        'ultimo_aggiornamento': datetime.now(timezone.utc).isoformat(),
        'sedute': all_sedute[:50],
        'interrogazioni': all_interrogazioni[:100],
        'mozioni': all_mozioni[:100],
        'statistiche': {
            'totale_sedute': len(all_sedute),
            'totale_interrogazioni': len([x for x in all_interrogazioni if x['tipo'] == 'interrogazione']),
            'totale_interpellanze': len([x for x in all_interrogazioni if x['tipo'] == 'interpellanza']),
            'totale_mozioni': len([x for x in all_mozioni if x['tipo'] == 'mozione']),
            'totale_odg': len([x for x in all_mozioni if x['tipo'] == 'ordine_del_giorno']),
            'mozioni_approvate': len([x for x in all_mozioni if x.get('stato') == 'Approvato']),
            'mozioni_respinte': len([x for x in all_mozioni if x.get('stato') == 'Respinto']),
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  Dati salvati in {output_path}")
    print(f"  Sedute: {len(all_sedute)}")
    print(f"  Interrogazioni/Interpellanze: {len(all_interrogazioni)}")
    print(f"  Mozioni/OdG: {len(all_mozioni)}")


if __name__ == '__main__':
    main()
