#!/bin/bash
# Script per avviare il Comparatore Distretti Industriali

# Verifica se le dipendenze sono installate
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "Installazione dipendenze..."
    pip install -r requirements.txt
fi

# Avvia l'applicazione
echo "Avvio Comparatore Distretti Industriali..."
echo "L'applicazione sarà disponibile su http://localhost:8501"
streamlit run app.py
