"""
Configurazione pipeline dati — Osservatorio Politico Piemonte.

Definisce le fonti RSS, le keyword per la classificazione tematica,
e i parametri per scraping e API.
"""

import os

# Directory di output per i dati auto-generati
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'auto')

# Feed RSS da monitorare
RSS_FEEDS = [
    {
        'id': 'regione',
        'nome': 'Regione Piemonte',
        'url': 'https://www.regione.piemonte.it/web/pinforma/feed',
        'colore': '#2563eb'
    },
    {
        'id': 'consiglio',
        'nome': 'Consiglio Regionale',
        'url': 'https://www.cr.piemonte.it/cms/rss.xml',
        'colore': '#7c3aed'
    },
    {
        'id': 'arpa',
        'nome': 'ARPA Piemonte',
        'url': 'https://www.arpa.piemonte.it/rss.xml',
        'colore': '#16a34a'
    },
    {
        'id': 'comune_torino',
        'nome': 'Comune di Torino',
        'url': 'https://www.comune.torino.it/novita/rss.xml',
        'colore': '#dc2626'
    },
    {
        'id': 'torinoclick',
        'nome': 'TorinoClick',
        'url': 'https://www.torinoclick.it/feed/',
        'colore': '#ea580c'
    }
]

# Fonti senza RSS (scraping)
SCRAPE_SOURCES = [
    {
        'id': 'ires',
        'nome': 'IRES Piemonte',
        'urls': [
            'https://www.ires.piemonte.it/categorie/news/',
            'https://www.ires.piemonte.it/ultime-pubblicazioni/',
        ],
        'colore': '#6366f1'
    },
    {
        'id': 'unioncamere',
        'nome': 'Unioncamere Piemonte',
        'urls': [
            'https://pie.camcom.it/notizie',
            'https://pie.camcom.it/comunicazione-e-stampa/comunicati-stampa',
        ],
        'colore': '#ca8a04'
    },
    {
        'id': 'consiglio_sedute',
        'nome': 'Resoconti sedute Consiglio Regionale',
        'urls': [
            'https://www.cr.piemonte.it/seduteconsiglio/appl/search/index.php',
        ],
        'colore': '#4f46e5'
    }
]

# Keyword per classificazione automatica notizie → tematiche
# Ogni tema ha una lista di keyword (case-insensitive)
TEMA_KEYWORDS = {
    'crisi-automotive': [
        'automotive', 'stellantis', 'mirafiori', 'fiat', 'auto elettrica',
        'filiera auto', 'componentistica', 'cassa integrazione automotive',
        'indotto auto', 'transizione industriale', 'veicoli elettrici',
        'produzione automobili', 'fondo formazione occupazione'
    ],
    'sanita-regionale': [
        'sanita', 'sanitario', 'ospedale', 'ospedali', 'asl', 'azienda sanitaria',
        'piano socio-sanitario', 'liste attesa', 'lista attesa', 'pronto soccorso',
        'parco salute', 'case comunita', 'casa comunita', 'caregiver',
        'medici', 'infermieri', 'posti letto', 'lea', 'prestazioni sanitarie'
    ],
    'bilancio-regionale': [
        'bilancio', 'bilancio regionale', 'bilancio previsione', 'disavanzo',
        'revisori conti', 'spesa regionale', 'entrate regionali', 'debito',
        'manovra', 'finanziaria', 'piano alienazioni', 'liquidita'
    ],
    'attivita-produttive': [
        'imprese', 'attivita produttive', 'pmi', 'startup', 'innovazione',
        'manifattura', 'distretti industriali', 'competitivita', 'investimenti'
    ],
    'commercio-artigianato': [
        'commercio', 'artigianato', 'botteghe', 'negozi', 'mercati',
        'commercio ambulante', 'fiere', 'esercizi commerciali'
    ],
    'agricoltura': [
        'agricoltura', 'agricolo', 'pac', 'sviluppo rurale', 'vino', 'vitivinicolo',
        'agroalimentare', 'allevamento', 'riso', 'cereali', 'biologico'
    ],
    'turismo': [
        'turismo', 'turistico', 'alberghi', 'ospitalita', 'tour operator',
        'destinazione', 'vacanze', 'enogastronomia', 'langhe', 'monferrato'
    ],
    'lavoro-occupazione': [
        'lavoro', 'occupazione', 'disoccupazione', 'precariato',
        'contratti', 'assunzioni', 'licenziamenti', 'sindacati',
        'politiche attive', 'garanzia giovani', 'gol', 'formazione lavoro'
    ],
    'energia': [
        'energia', 'energetico', 'rinnovabili', 'fotovoltaico', 'eolico',
        'gas', 'bollette', 'comunita energetiche', 'transizione energetica'
    ],
    'trasporti-mobilita': [
        'trasporti', 'mobilita', 'treni', 'autobus', 'tpl', 'ferrovie',
        'metropolitana', 'ciclabilita', 'pendolari', 'infrastrutture viarie',
        'autostrade', 'piemove'
    ],
    'istruzione-formazione': [
        'istruzione', 'scuola', 'scuole', 'formazione professionale',
        'its', 'diritto studio', 'edilizia scolastica', 'dispersione scolastica',
        'orientamento', 'pcto'
    ],
    'edilizia-opere-pubbliche': [
        'edilizia', 'opere pubbliche', 'infrastrutture', 'cantieri',
        'edilizia residenziale', 'edilizia popolare', 'housing', 'urbanistica'
    ],
    'sociale-welfare': [
        'sociale', 'welfare', 'assistenza', 'disabilita', 'anziani',
        'minori', 'famiglie', 'reddito', 'poverta', 'inclusione',
        'servizi sociali', 'terzo settore', 'volontariato'
    ],
    'ambiente-qualita-aria': [
        'ambiente', 'inquinamento', 'qualita aria', 'pm10', 'pm2.5',
        'smog', 'emissioni', 'rifiuti', 'raccolta differenziata',
        'prqa', 'piano aria', 'blocco traffico', 'diesel'
    ],
    'pianificazione-territoriale': [
        'pianificazione territoriale', 'piano regolatore', 'consumo suolo',
        'rigenerazione urbana', 'territorio', 'aree dismesse'
    ],
    'enti-locali-piccoli-comuni': [
        'comuni', 'enti locali', 'sindaci', 'piccoli comuni', 'aree interne',
        'spopolamento', 'unioni montane', 'citta metropolitana', 'province'
    ],
    'montagna': [
        'montagna', 'alpeggi', 'stazioni sciistiche', 'comprensori',
        'olimpiadi invernali', 'neve', 'rifugi', 'sentieri'
    ],
    'protezione-civile': [
        'protezione civile', 'alluvione', 'frana', 'rischio idrogeologico',
        'emergenza', 'esondazione', 'incendi boschivi', 'calamita'
    ],
    'fondi-europei': [
        'fondi europei', 'pnrr', 'fsc', 'fesr', 'fse', 'fondi strutturali',
        'coesione', 'next generation', 'pac', 'europrogettazione'
    ],
    'autonomia-differenziata': [
        'autonomia differenziata', 'autonomia regionale', 'articolo 116',
        'devoluzione', 'competenze regionali', 'lep'
    ],
    'organizzazione-regionale': [
        'organizzazione regionale', 'personale regionale', 'dirigenti',
        'ente regione', 'riforma amministrativa', 'digitalizzazione pa'
    ],
    'trasparenza': [
        'trasparenza', 'anticorruzione', 'accesso atti', 'partecipazione',
        'open government', 'accountability', 'societa partecipate'
    ],
    'cultura-beni-culturali': [
        'cultura', 'beni culturali', 'musei', 'biblioteche', 'teatro',
        'patrimonio culturale', 'restauro', 'arte', 'spettacolo'
    ],
    'sport': [
        'sport', 'impianti sportivi', 'atp finals', 'olimpiadi',
        'associazioni sportive', 'calcio', 'pallavolo'
    ],
    'universita-ricerca': [
        'universita', 'ricerca', 'politecnico', 'unito', 'atenei',
        'spin-off', 'brevetti', 'incubatori', 'i3p', 'nodes'
    ],
    'giovani': [
        'giovani', 'giovanile', 'neet', 'under 30', 'politiche giovanili',
        'servizio civile', 'spazi giovani'
    ],
    'pari-opportunita': [
        'pari opportunita', 'parita genere', 'violenza donne',
        'gap salariale', 'conciliazione', 'diritti civili', 'lgbtq'
    ]
}

# Pesi per le fonti nel calcolo rilevanza briefing
# Fonti istituzionali primarie pesano di più
FONTE_WEIGHTS = {
    'regione': 3,
    'consiglio': 3,
    'comune_torino': 2,
    'torinoclick': 2,
    'arpa': 2,
    'ires': 2,
    'unioncamere': 2,
    'consiglio_sedute': 3,
}

# Temi "caldi" che pesano di più nel briefing
TEMI_CALDI = [
    'sanita-regionale', 'bilancio-regionale', 'lavoro-occupazione',
    'crisi-automotive', 'fondi-europei'
]

# Stazioni ARPA per monitoraggio qualita aria
ARPA_STAZIONI = [
    {'id': 'TO_001', 'nome': 'Torino - Lingotto', 'provincia': 'TO'},
    {'id': 'TO_002', 'nome': 'Torino - Consolata', 'provincia': 'TO'},
    {'id': 'TO_003', 'nome': 'Torino - Rebaudengo', 'provincia': 'TO'},
]

# URL Open Data Torino
TORINO_OPENDATA_BASE = 'https://servizi.comune.torino.it/consiglio/prg/documenti/documentazione/opendata'
TORINO_DATASETS = ['atti', 'votazioni', 'presenze', 'sedute']

# API dati.piemonte.it
DATI_PIEMONTE_API = 'https://dati.piemonte.it/api'
