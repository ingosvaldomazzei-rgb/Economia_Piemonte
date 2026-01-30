# Comparatore Distretti Industriali del Piemonte

Applicazione interattiva per l'analisi e il confronto dei principali distretti industriali della Regione Piemonte.

## Funzionalità

- **Dashboard**: Panoramica generale con metriche aggregate
- **Confronta Distretti**: Confronto multiplo con grafici interattivi (barre, radar, heatmap, scatter)
- **Dettaglio Distretto**: Scheda completa con KPI, trend storici e analisi SWOT
- **Gestione Dati**: Aggiungi, modifica, elimina distretti con persistenza automatica
- **Storico Modifiche**: Tracciamento di tutte le modifiche effettuate

## Distretti Inclusi

| Distretto | Settore | Provincia |
|-----------|---------|-----------|
| Automotive | Automotive | Torino |
| Aerospaziale | Aerospazio | Torino |
| Tessile Biellese | Tessile-Abbigliamento | Biella |
| Orafo di Valenza | Oreficeria-Gioielleria | Alessandria |
| Rubinetto | Rubinetteria-Valvolame | VCO |
| Agroalimentare Langhe-Roero | Alimentare-Vitivinicolo | Cuneo |
| ICT e Meccatronica | ICT-Meccatronica | Torino |
| Gomma-Plastica | Gomma-Plastica | Torino |

## Installazione Locale

```bash
# Clona il repository
git clone https://github.com/ingosvaldomazzei-rgb/Economia_Piemonte.git
cd Economia_Piemonte/comparatore_distretti

# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
streamlit run app.py
```

L'applicazione sarà disponibile su http://localhost:8501

## Tecnologie

- **Streamlit** - Framework per l'interfaccia web
- **Plotly** - Grafici interattivi
- **Pandas** - Gestione e analisi dati
- **JSON** - Persistenza dati

## Struttura Progetto

```
comparatore_distretti/
├── app.py                 # Applicazione principale
├── requirements.txt       # Dipendenze Python
├── .streamlit/
│   └── config.toml        # Configurazione Streamlit
├── data/
│   ├── distretti.json     # Dati distretti
│   ├── benchmark.json     # Benchmark nazionali/europei
│   └── storico.json       # Log modifiche
└── utils/
    ├── data_manager.py    # Gestione persistenza dati
    └── charts.py          # Generazione grafici
```

## Licenza

Progetto per analisi economica della Regione Piemonte.
