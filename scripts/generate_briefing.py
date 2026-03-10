"""
Genera il briefing settimanale delle notizie più rilevanti.

Input: src/data/auto/notizie.json, notizie-per-tema.json
Output: src/data/auto/briefing.json
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR, FONTE_WEIGHTS, TEMA_KEYWORDS, TEMI_CALDI


def get_week_range():
    """Calcola inizio e fine della settimana corrente (lunedì-domenica)."""
    now = datetime.now(timezone.utc)
    # Vai a 7 giorni fa
    start = now - timedelta(days=7)
    return start, now


def classify_notizia(notizia):
    """Classifica una notizia restituendo i temi associati."""
    testo = (notizia.get('titolo', '') + ' ' + notizia.get('descrizione', '')).lower()
    temi = []
    for tema, keywords in TEMA_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in testo:
                temi.append(tema)
                break
    return temi


def compute_relevance(notizia, temi, all_titles, now):
    """Calcola il punteggio di rilevanza di una notizia."""
    score = 0.0

    # 1. Peso della fonte
    fonte_id = notizia.get('fonte_id', '')
    score += FONTE_WEIGHTS.get(fonte_id, 1)

    # 2. Temi caldi
    for tema in temi:
        if tema in TEMI_CALDI:
            score += 1.5
            break

    # 3. Cross-referencing: parole chiave del titolo che compaiono in altri titoli
    titolo_words = set(re.findall(r'\b\w{4,}\b', notizia.get('titolo', '').lower()))
    # Escludi parole comuni
    stop_words = {'della', 'delle', 'dello', 'degli', 'nella', 'nelle', 'nello',
                  'negli', 'dalla', 'dalle', 'dallo', 'dagli', 'sulla', 'sulle',
                  'sullo', 'sugli', 'sono', 'stato', 'stata', 'stati', 'state',
                  'come', 'anche', 'dopo', 'prima', 'ogni', 'questa', 'questo',
                  'piemonte', 'regione', 'torino', 'regionale', 'piemontese',
                  'tutto', 'tutti', 'tutte', 'nuovo', 'nuova', 'nuovi', 'nuove',
                  'anno', 'anni', 'mese', 'mesi', 'giorno', 'giorni'}
    titolo_words -= stop_words

    cross_count = 0
    for other_title_words in all_titles:
        if other_title_words == titolo_words:
            continue
        overlap = titolo_words & other_title_words
        if len(overlap) >= 2:
            cross_count += 1

    if cross_count >= 2:
        score += 2.0
    elif cross_count >= 1:
        score += 1.0

    # 4. Recenza (bonus per notizie più recenti)
    try:
        pub_date = datetime.fromisoformat(notizia.get('data', ''))
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        days_ago = (now - pub_date).days
        if days_ago <= 1:
            score += 1.0
        elif days_ago <= 3:
            score += 0.5
    except (ValueError, TypeError):
        pass

    return score


def generate_briefing_data(notizie, start_date, end_date):
    """Genera i dati strutturati del briefing."""
    now = datetime.now(timezone.utc)

    # Filtra notizie degli ultimi 7 giorni
    week_news = []
    for n in notizie:
        try:
            pub_date = datetime.fromisoformat(n.get('data', ''))
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            if start_date <= pub_date <= end_date:
                week_news.append(n)
        except (ValueError, TypeError):
            continue

    if not week_news:
        return None

    # Pre-calcola parole dei titoli per cross-referencing
    all_titles = []
    for n in week_news:
        words = set(re.findall(r'\b\w{4,}\b', n.get('titolo', '').lower()))
        all_titles.append(words)

    # Classifica e calcola rilevanza
    scored_news = []
    news_by_tema = defaultdict(list)

    for i, n in enumerate(week_news):
        temi = classify_notizia(n)
        relevance = compute_relevance(n, temi, all_titles, now)
        entry = {**n, '_score': relevance, '_temi': temi}
        scored_news.append(entry)

        if not temi:
            news_by_tema['altro'].append(entry)
        for tema in temi:
            news_by_tema[tema].append(entry)

    # Seleziona le top 10 notizie più rilevanti (uniche)
    scored_news.sort(key=lambda x: x['_score'], reverse=True)
    top_ids = set()
    top_news = []
    for n in scored_news:
        if n['id'] not in top_ids and len(top_news) < 10:
            top_ids.add(n['id'])
            top_news.append(n)

    # Organizza per tema
    temi_briefing = []

    # Mappa temi a nomi leggibili
    tema_labels = {
        'sanita-regionale': 'Sanita',
        'bilancio-regionale': 'Bilancio Regionale',
        'lavoro-occupazione': 'Lavoro & Occupazione',
        'crisi-automotive': 'Automotive',
        'attivita-produttive': 'Attivita Produttive',
        'commercio-artigianato': 'Commercio & Artigianato',
        'agricoltura': 'Agricoltura',
        'turismo': 'Turismo',
        'energia': 'Energia',
        'trasporti-mobilita': 'Trasporti & Mobilita',
        'istruzione-formazione': 'Istruzione & Formazione',
        'edilizia-opere-pubbliche': 'Edilizia & Opere Pubbliche',
        'sociale-welfare': 'Sociale & Welfare',
        'ambiente-qualita-aria': 'Ambiente & Qualita Aria',
        'pianificazione-territoriale': 'Pianificazione Territoriale',
        'enti-locali-piccoli-comuni': 'Enti Locali',
        'montagna': 'Montagna',
        'protezione-civile': 'Protezione Civile',
        'fondi-europei': 'Fondi Europei & PNRR',
        'autonomia-differenziata': 'Autonomia Differenziata',
        'organizzazione-regionale': 'Organizzazione Regionale',
        'trasparenza': 'Trasparenza',
        'cultura-beni-culturali': 'Cultura & Beni Culturali',
        'sport': 'Sport',
        'universita-ricerca': 'Universita & Ricerca',
        'giovani': 'Giovani',
        'pari-opportunita': 'Pari Opportunita',
        'altro': 'Altro',
    }

    # Tema icons
    tema_icons = {
        'sanita-regionale': 'heart',
        'bilancio-regionale': 'banknotes',
        'lavoro-occupazione': 'briefcase',
        'crisi-automotive': 'truck',
        'attivita-produttive': 'building',
        'energia': 'bolt',
        'trasporti-mobilita': 'train',
        'ambiente-qualita-aria': 'leaf',
        'fondi-europei': 'globe',
        'cultura-beni-culturali': 'palette',
        'sport': 'trophy',
        'universita-ricerca': 'academic',
    }

    # Raggruppa le top news per tema
    tema_to_top = defaultdict(list)
    for n in top_news:
        temi = n['_temi']
        if not temi:
            tema_to_top['altro'].append(n)
        else:
            tema_to_top[temi[0]].append(n)

    for tema_slug, news_list in sorted(tema_to_top.items(),
                                        key=lambda x: len(x[1]), reverse=True):
        temi_briefing.append({
            'slug': tema_slug,
            'label': tema_labels.get(tema_slug, tema_slug.replace('-', ' ').title()),
            'icon': tema_icons.get(tema_slug, 'newspaper'),
            'notizie': [{
                'id': n['id'],
                'titolo': n['titolo'],
                'link': n['link'],
                'descrizione': n.get('descrizione', ''),
                'data': n['data'],
                'fonte': n['fonte'],
                'fonte_id': n['fonte_id'],
                'score': round(n['_score'], 1),
            } for n in news_list]
        })

    # Statistiche
    per_fonte = Counter(n.get('fonte', 'Sconosciuto') for n in week_news)
    per_tema_count = {}
    for tema, news_list in news_by_tema.items():
        label = tema_labels.get(tema, tema.replace('-', ' ').title())
        per_tema_count[label] = len(news_list)

    # Formato date italiane
    def format_date_it(dt):
        mesi = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
                'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
        return f"{dt.day} {mesi[dt.month - 1]} {dt.year}"

    briefing = {
        'titolo': f"Briefing Settimanale",
        'data_inizio': format_date_it(start_date),
        'data_fine': format_date_it(end_date),
        'data_inizio_iso': start_date.isoformat(),
        'data_fine_iso': end_date.isoformat(),
        'generato_il': now.isoformat(),
        'generato_il_it': now.strftime('%d/%m/%Y ore %H:%M'),
        'temi': temi_briefing,
        'statistiche': {
            'totale_notizie': len(week_news),
            'per_fonte': dict(per_fonte.most_common()),
            'per_tema': dict(sorted(per_tema_count.items(), key=lambda x: x[1], reverse=True)),
        }
    }

    return briefing


def main():
    print("=== Generazione Briefing Settimanale ===")

    notizie_path = os.path.join(DATA_DIR, 'notizie.json')
    if not os.path.exists(notizie_path):
        print("Nessun file notizie.json trovato. Esegui prima fetch_rss.py")
        return

    with open(notizie_path, 'r', encoding='utf-8') as f:
        notizie = json.load(f)

    start_date, end_date = get_week_range()
    print(f"  Periodo: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")

    briefing = generate_briefing_data(notizie, start_date, end_date)

    # Carica archivio briefing precedenti
    archivio_path = os.path.join(DATA_DIR, 'briefing-archivio.json')
    archivio = []
    if os.path.exists(archivio_path):
        with open(archivio_path, 'r', encoding='utf-8') as f:
            archivio = json.load(f)

    if briefing:
        # Aggiungi il briefing corrente all'archivio (evita duplicati per stessa settimana)
        archivio = [b for b in archivio
                     if b.get('data_inizio_iso', '') != briefing['data_inizio_iso']]
        archivio.insert(0, briefing)
        # Mantieni max 8 settimane di archivio
        archivio = archivio[:8]

        print(f"  Notizie nella settimana: {briefing['statistiche']['totale_notizie']}")
        print(f"  Temi nel briefing: {len(briefing['temi'])}")
        for tema in briefing['temi']:
            print(f"    {tema['label']}: {len(tema['notizie'])} notizie selezionate")
    else:
        print("  Nessuna notizia trovata per questa settimana.")
        briefing = {
            'titolo': 'Briefing Settimanale',
            'data_inizio': start_date.strftime('%d/%m/%Y'),
            'data_fine': end_date.strftime('%d/%m/%Y'),
            'data_inizio_iso': start_date.isoformat(),
            'data_fine_iso': end_date.isoformat(),
            'generato_il': datetime.now(timezone.utc).isoformat(),
            'generato_il_it': datetime.now(timezone.utc).strftime('%d/%m/%Y ore %H:%M'),
            'temi': [],
            'statistiche': {'totale_notizie': 0, 'per_fonte': {}, 'per_tema': {}}
        }

    # Salva briefing corrente
    briefing_path = os.path.join(DATA_DIR, 'briefing.json')
    with open(briefing_path, 'w', encoding='utf-8') as f:
        json.dump(briefing, f, ensure_ascii=False, indent=2)

    # Salva archivio
    with open(archivio_path, 'w', encoding='utf-8') as f:
        json.dump(archivio, f, ensure_ascii=False, indent=2)

    print(f"\n  Briefing salvato in {briefing_path}")
    print(f"  Archivio ({len(archivio)} briefing) in {archivio_path}")


if __name__ == '__main__':
    main()
