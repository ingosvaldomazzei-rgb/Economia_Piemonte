"""
Kanban Dashboard Interattiva
Una semplice board per gestire le tue attività
"""

import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Kanban Board",
    page_icon="📋",
    layout="wide"
)

# Inizializza lo stato della sessione (memoria delle attività)
if "tasks" not in st.session_state:
    st.session_state.tasks = {
        "da_fare": ["Esempio: Prima attività", "Esempio: Seconda attività"],
        "in_corso": ["Esempio: Attività in lavorazione"],
        "fatto": ["Esempio: Attività completata"]
    }

# Titolo principale
st.title("📋 Kanban Board")
st.markdown("---")

# Sezione per aggiungere nuove attività
st.subheader("➕ Aggiungi nuova attività")
col_input, col_button = st.columns([3, 1])

with col_input:
    nuova_attivita = st.text_input("Descrizione attività", label_visibility="collapsed", placeholder="Scrivi qui la nuova attività...")

with col_button:
    if st.button("Aggiungi", type="primary", use_container_width=True):
        if nuova_attivita.strip():
            st.session_state.tasks["da_fare"].append(nuova_attivita)
            st.rerun()

st.markdown("---")

# Funzione per spostare un'attività
def sposta_attivita(task, da_colonna, a_colonna):
    st.session_state.tasks[da_colonna].remove(task)
    st.session_state.tasks[a_colonna].append(task)

# Funzione per eliminare un'attività
def elimina_attivita(task, colonna):
    st.session_state.tasks[colonna].remove(task)

# Creo le tre colonne del Kanban
col1, col2, col3 = st.columns(3)

# Colonna 1: DA FARE
with col1:
    st.markdown("### 📝 Da Fare")
    st.markdown(f"*{len(st.session_state.tasks['da_fare'])} attività*")

    for i, task in enumerate(st.session_state.tasks["da_fare"]):
        with st.container(border=True):
            st.write(task)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("▶️", key=f"start_{i}", help="Inizia"):
                    sposta_attivita(task, "da_fare", "in_corso")
                    st.rerun()
            with c2:
                if st.button("✅", key=f"done_{i}", help="Completato"):
                    sposta_attivita(task, "da_fare", "fatto")
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"del_todo_{i}", help="Elimina"):
                    elimina_attivita(task, "da_fare")
                    st.rerun()

# Colonna 2: IN CORSO
with col2:
    st.markdown("### 🔄 In Corso")
    st.markdown(f"*{len(st.session_state.tasks['in_corso'])} attività*")

    for i, task in enumerate(st.session_state.tasks["in_corso"]):
        with st.container(border=True):
            st.write(task)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("◀️", key=f"back_{i}", help="Torna indietro"):
                    sposta_attivita(task, "in_corso", "da_fare")
                    st.rerun()
            with c2:
                if st.button("✅", key=f"complete_{i}", help="Completato"):
                    sposta_attivita(task, "in_corso", "fatto")
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"del_prog_{i}", help="Elimina"):
                    elimina_attivita(task, "in_corso")
                    st.rerun()

# Colonna 3: FATTO
with col3:
    st.markdown("### ✅ Fatto")
    st.markdown(f"*{len(st.session_state.tasks['fatto'])} attività*")

    for i, task in enumerate(st.session_state.tasks["fatto"]):
        with st.container(border=True):
            st.write(task)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("◀️", key=f"reopen_{i}", help="Riapri"):
                    sposta_attivita(task, "fatto", "in_corso")
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_done_{i}", help="Elimina"):
                    elimina_attivita(task, "fatto")
                    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Kanban Board creata con Python e Streamlit* 🐍")
