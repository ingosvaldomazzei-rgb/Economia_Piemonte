"""
Scraping leggero per fonti senza feed RSS (IRES Piemonte, Unioncamere Piemonte).

Output: integrato in src/data/auto/notizie.json (stesso formato di fetch_rss.py)
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

sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR, SCRAPE_SOURCES

REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 2  # secondi tra richieste allo stesso dominio

HEADERS = {
    'User-Agent': 'OsservatorioPiemonte/1.0 (monitoraggio istituzionale; contatto: osservatorio@example.it)'
}


def scrape_ires_page(url, source_config):
    """Scrape notizie/pubblicazioni dalla pagina IRES Piemonte."""
    notizie = []
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # IRES usa card con titoli linkati
        articles = soup.select('article, .post, .entry, .news-item, .card')
        if not articles:
            # fallback: cerca tutti i link con titoli significativi
            articles = soup.select('.content a[href], .main a[href], #content a[href]')

        for art in articles[:20]:
            titolo_el = art.find(['h2', 'h3', 'h4', 'a'])
            if not titolo_el:
                continue

            titolo = titolo_el.get_text(strip=True)
            if not titolo or len(titolo) < 10:
                continue

            link = ''
            link_el = art.find('a', href=True) if art.name != 'a' else art
            if link_el:
                href = link_el.get('href', '')
                if href.startswith('/'):
                    link = 'https://www.ires.piemonte.it' + href
                elif href.startswith('http'):
                    link = href
                else:
                    continue
            else:
                continue

            # Descrizione
            desc_el = art.find(['p', '.excerpt', '.summary'])
            descrizione = desc_el.get_text(strip=True)[:500] if desc_el else ''

            # Data - cerca nel testo
            data = datetime.now(timezone.utc).isoformat()
            date_el = art.find(['time', '.date', '.data', 'span'])
            if date_el:
                date_text = date_el.get_text(strip=True)
                parsed = _try_parse_date(date_text)
                if parsed:
                    data = parsed

            notizia_id = md5(link.encode()).hexdigest()[:12]
            notizie.append({
                'id': notizia_id,
                'titolo': titolo,
                'link': link,
                'descrizione': descrizione,
                'data': data,
                'fonte': source_config['nome'],
                'fonte_id': source_config['id'],
                'colore': source_config['colore']
            })

    except Exception as e:
        print(f"  ERRORE scraping {url}: {e}")

    return notizie


def scrape_unioncamere_page(url, source_config):
    """Scrape notizie/comunicati da Unioncamere Piemonte (pie.camcom.it)."""
    notizie = []
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        articles = soup.select('article, .node, .views-row, .news-item, .card, .list-item')
        if not articles:
            articles = soup.select('.view-content .views-row, .content a[href]')

        for art in articles[:20]:
            titolo_el = art.find(['h2', 'h3', 'h4', 'a'])
            if not titolo_el:
                continue

            titolo = titolo_el.get_text(strip=True)
            if not titolo or len(titolo) < 10:
                continue

            link = ''
            link_el = art.find('a', href=True) if art.name != 'a' else art
            if link_el:
                href = link_el.get('href', '')
                if href.startswith('/'):
                    link = 'https://pie.camcom.it' + href
                elif href.startswith('http'):
                    link = href
                else:
                    continue
            else:
                continue

            desc_el = art.find(['p', '.field-body', '.summary'])
            descrizione = desc_el.get_text(strip=True)[:500] if desc_el else ''

            data = datetime.now(timezone.utc).isoformat()
            date_el = art.find(['time', '.date', '.data', 'span'])
            if date_el:
                date_text = date_el.get_text(strip=True)
                parsed = _try_parse_date(date_text)
                if parsed:
                    data = parsed

            notizia_id = md5(link.encode()).hexdigest()[:12]
            notizie.append({
                'id': notizia_id,
                'titolo': titolo,
                'link': link,
                'descrizione': descrizione,
                'data': data,
                'fonte': source_config['nome'],
                'fonte_id': source_config['id'],
                'colore': source_config['colore']
            })

    except Exception as e:
        print(f"  ERRORE scraping {url}: {e}")

    return notizie


def scrape_consiglio_sedute_page(url, source_config):
    """Scrape resoconti sedute del Consiglio Regionale."""
    notizie = []
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        selectors = [
            '.results .item', '.result', '.search-result',
            'table tr', 'article', '.elenco-sedute li', '.list-group-item'
        ]
        items = []
        for sel in selectors:
            items = soup.select(sel)
            if items:
                break

        if not items:
            items = soup.select('a[href*="seduta"], a[href*="resoconto"], a[href*="verbale"]')

        for item in items[:40]:
            link_el = item if getattr(item, 'name', None) == 'a' else item.find('a', href=True)
            if not link_el:
                continue

            titolo = link_el.get_text(' ', strip=True)
            href = (link_el.get('href') or '').strip()
            if not titolo or len(titolo) < 8 or not href:
                continue

            if href.startswith('/'):
                link = 'https://www.cr.piemonte.it' + href
            elif href.startswith('http'):
                link = href
            else:
                continue

            titolo_l = titolo.lower()
            if not any(k in titolo_l for k in ['seduta', 'resoconto', 'verbale', 'consiglio']):
                continue

            descrizione = ''
            desc_el = item.find(['p', 'td', 'div', 'span']) if getattr(item, 'name', None) != 'a' else None
            if desc_el:
                descrizione = desc_el.get_text(' ', strip=True)[:500]

            data = datetime.now(timezone.utc).isoformat()
            date_candidates = []
            if getattr(item, 'name', None) != 'a':
                date_candidates.extend(item.find_all(['time', 'span', 'td']))
            for date_el in date_candidates[:4]:
                parsed = _try_parse_date(date_el.get_text(' ', strip=True))
                if parsed:
                    data = parsed
                    break

            notizia_id = md5(link.encode()).hexdigest()[:12]
            notizie.append({
                'id': notizia_id,
                'titolo': titolo,
                'link': link,
                'descrizione': descrizione,
                'data': data,
                'fonte': source_config['nome'],
                'fonte_id': source_config['id'],
                'colore': source_config['colore']
            })

    except Exception as e:
        print(f"  ERRORE scraping {url}: {e}")

    return notizie


def _try_parse_date(text):
    """Prova a parsare una data da testo italiano o formato ISO."""
    if not text:
        return None

    # Mesi italiani
    mesi = {
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
        'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
        'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12',
        'gen': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'mag': '05', 'giu': '06', 'lug': '07', 'ago': '08',
        'set': '09', 'ott': '10', 'nov': '11', 'dic': '12',
    }

    text = text.strip().lower()

    # Formato: "3 marzo 2026" o "03/03/2026"
    for mese_nome, mese_num in mesi.items():
        match = re.search(rf'(\d{{1,2}})\s+{mese_nome}\s+(\d{{4}})', text)
        if match:
            try:
                d = datetime(int(match.group(2)), int(mese_num), int(match.group(1)), tzinfo=timezone.utc)
                return d.isoformat()
            except ValueError:
                pass

    # Formato dd/mm/yyyy
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if match:
        try:
            d = datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)), tzinfo=timezone.utc)
            return d.isoformat()
        except ValueError:
            pass

    # Formato ISO
    match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if match:
        try:
            d = datetime.fromisoformat(match.group(1)).replace(tzinfo=timezone.utc)
            return d.isoformat()
        except ValueError:
            pass

    return None


def main():
    print("=== Scraping Fonti senza RSS ===")

    os.makedirs(DATA_DIR, exist_ok=True)

    # Carica notizie esistenti per merge
    notizie_path = os.path.join(DATA_DIR, 'notizie.json')
    existing = {}
    if os.path.exists(notizie_path):
        with open(notizie_path, 'r', encoding='utf-8') as f:
            for n in json.load(f):
                existing[n['id']] = n

    nuove_totali = 0
    for source in SCRAPE_SOURCES:
        print(f"\n  Fonte: {source['nome']}")
        for url in source['urls']:
            print(f"    Scraping {url}...")

            if source['id'] == 'ires':
                notizie = scrape_ires_page(url, source)
            elif source['id'] == 'unioncamere':
                notizie = scrape_unioncamere_page(url, source)
            elif source['id'] == 'consiglio_sedute':
                notizie = scrape_consiglio_sedute_page(url, source)
            else:
                notizie = []

            for n in notizie:
                existing[n['id']] = n
            nuove_totali += len(notizie)
            print(f"    -> {len(notizie)} notizie trovate")

            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Salva (ordinate per data, max 200 per includere tutte le fonti)
    tutte = sorted(existing.values(), key=lambda x: x.get('data', ''), reverse=True)
    tutte = tutte[:200]

    with open(notizie_path, 'w', encoding='utf-8') as f:
        json.dump(tutte, f, ensure_ascii=False, indent=2)

    print(f"\nScraping completato: {nuove_totali} notizie raccolte")
    print(f"Totale in archivio: {len(tutte)} notizie")


if __name__ == '__main__':
    main()
