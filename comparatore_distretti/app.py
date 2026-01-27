"""
Comparatore Distretti Industriali del Piemonte
Applicazione Streamlit per analisi e confronto dei distretti industriali.

Avvio: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Aggiungi il percorso per gli import
sys.path.insert(0, str(Path(__file__).parent))

from utils.data_manager import DataManager
from utils.charts import ChartManager

# === CONFIGURAZIONE PAGINA ===
st.set_page_config(
    page_title="Comparatore Distretti Industriali - Piemonte",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === INIZIALIZZAZIONE ===
@st.cache_resource
def get_data_manager():
    """Inizializza il DataManager (cached)."""
    return DataManager()

dm = get_data_manager()
charts = ChartManager()

# === STILI CSS CUSTOM ===
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9em;
        opacity: 0.9;
    }
    .section-header {
        border-left: 4px solid #667eea;
        padding-left: 15px;
        margin: 20px 0;
    }
    .highlight-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Regione-Piemonte-Stemma.svg/150px-Regione-Piemonte-Stemma.svg.png", width=80)
    st.title("🏭 Comparatore Distretti")
    st.markdown("---")

    # Navigazione
    pagina = st.radio(
        "📍 Navigazione",
        ["🏠 Dashboard", "📊 Confronta Distretti", "🔍 Dettaglio Distretto", "✏️ Gestione Dati", "📜 Storico Modifiche"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Info rapide
    stats = dm.get_statistiche_generali()
    if stats:
        st.metric("Distretti Monitorati", stats.get("num_distretti", 0))
        st.metric("Totale Imprese", f"{stats.get('totale_imprese', 0):,}")
        st.metric("Totale Addetti", f"{stats.get('totale_addetti', 0):,}")

    st.markdown("---")
    st.caption("v1.0 - Economia Piemonte")


# === PAGINA: DASHBOARD ===
def pagina_dashboard():
    st.title("🏠 Dashboard Distretti Industriali del Piemonte")
    st.markdown("Panoramica generale dei principali distretti industriali della regione.")

    distretti = dm.get_all_distretti()

    if not distretti:
        st.warning("Nessun distretto presente. Vai alla sezione 'Gestione Dati' per aggiungerne.")
        return

    # Metriche principali
    stats = dm.get_statistiche_generali()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏭 Distretti", stats.get("num_distretti", 0))
    with col2:
        st.metric("🏢 Imprese", f"{stats.get('totale_imprese', 0):,}")
    with col3:
        st.metric("👥 Addetti", f"{stats.get('totale_addetti', 0):,}")
    with col4:
        st.metric("💰 Fatturato", f"€{stats.get('totale_fatturato', 0):,.0f}M")

    st.markdown("---")

    # Grafici overview
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Fatturato per Distretto")
        fig = charts.bar_comparison(distretti, "fatturato_mln", "Fatturato (Milioni €)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("👥 Distribuzione Addetti")
        fig = charts.pie_distribution(distretti, "addetti", "Addetti per Distretto")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabella riepilogativa
    st.subheader("📋 Riepilogo Distretti")

    df_data = []
    for d in distretti:
        kpi = d.get("kpi", {})
        df_data.append({
            "Distretto": d.get("nome", "N/D"),
            "Settore": d.get("settore", "N/D"),
            "Provincia": d.get("provincia", "N/D"),
            "Imprese": kpi.get("num_imprese", 0),
            "Addetti": kpi.get("addetti", 0),
            "Fatturato (M€)": kpi.get("fatturato_mln", 0),
            "Export (M€)": kpi.get("export_mln", 0),
            "Export %": f"{kpi.get('export_percentuale', 0):.1f}%",
            "Crescita YoY": f"{kpi.get('crescita_yoy', 0):+.1f}%"
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


# === PAGINA: CONFRONTA DISTRETTI ===
def pagina_confronto():
    st.title("📊 Confronta Distretti")
    st.markdown("Seleziona i distretti e i KPI per un confronto dettagliato.")

    distretti = dm.get_all_distretti()

    if len(distretti) < 2:
        st.warning("Sono necessari almeno 2 distretti per il confronto.")
        return

    # Selezione distretti
    col1, col2 = st.columns([2, 1])

    with col1:
        nomi_distretti = {d.get("nome"): d.get("id") for d in distretti}
        selected_names = st.multiselect(
            "🏭 Seleziona Distretti da confrontare",
            options=list(nomi_distretti.keys()),
            default=list(nomi_distretti.keys())[:3]
        )
        selected_ids = [nomi_distretti[n] for n in selected_names]

    with col2:
        show_benchmark = st.checkbox("📈 Mostra Benchmark", value=True)
        benchmark_type = st.radio(
            "Tipo Benchmark",
            ["Nazionale", "Europeo"],
            horizontal=True,
            disabled=not show_benchmark
        )

    if len(selected_ids) < 2:
        st.info("Seleziona almeno 2 distretti per il confronto.")
        return

    selected_distretti = dm.get_distretti_by_ids(selected_ids)

    st.markdown("---")

    # KPI disponibili
    kpi_options = {
        "num_imprese": "Numero Imprese",
        "addetti": "Addetti",
        "fatturato_mln": "Fatturato (M€)",
        "export_mln": "Export (M€)",
        "export_percentuale": "Export %",
        "produttivita": "Produttività (k€/addetto)",
        "investimenti_rd_mln": "Investimenti R&D (M€)",
        "crescita_yoy": "Crescita YoY %",
        "quota_mercato_nazionale": "Quota Mercato Nazionale %"
    }

    # Tab per diversi tipi di confronto
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Barre", "🎯 Radar", "🔥 Heatmap", "📈 Correlazione"])

    with tab1:
        col1, col2 = st.columns([3, 1])
        with col2:
            selected_kpi = st.selectbox(
                "Seleziona KPI",
                options=list(kpi_options.keys()),
                format_func=lambda x: kpi_options[x],
                key="bar_kpi"
            )

        # Recupera benchmark se richiesto
        benchmark_value = None
        if show_benchmark and selected_distretti:
            settore = selected_distretti[0].get("settore")
            bench_data = dm.get_benchmark("nazionali" if benchmark_type == "Nazionale" else "europei")
            if settore in bench_data:
                # Mappa KPI a benchmark
                kpi_to_bench = {
                    "produttivita": "produttivita",
                    "export_percentuale": "export_percentuale",
                    "crescita_yoy": "crescita_media"
                }
                if selected_kpi in kpi_to_bench:
                    benchmark_value = bench_data[settore].get(kpi_to_bench[selected_kpi])

        fig = charts.bar_comparison(
            selected_distretti, selected_kpi,
            f"Confronto {kpi_options[selected_kpi]}",
            show_benchmark=show_benchmark,
            benchmark_value=benchmark_value
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns([3, 1])
        with col2:
            radar_kpis = st.multiselect(
                "KPI per Radar",
                options=list(kpi_options.keys()),
                default=["fatturato_mln", "addetti", "export_percentuale", "produttivita", "crescita_yoy"],
                format_func=lambda x: kpi_options[x],
                key="radar_kpis"
            )
            normalize_radar = st.checkbox("Normalizza valori", value=True, key="radar_norm")

        if len(radar_kpis) >= 3:
            fig = charts.radar_comparison(selected_distretti, radar_kpis, normalize=normalize_radar)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Seleziona almeno 3 KPI per il grafico radar.")

    with tab3:
        col1, col2 = st.columns([3, 1])
        with col2:
            heatmap_kpis = st.multiselect(
                "KPI per Heatmap",
                options=list(kpi_options.keys()),
                default=list(kpi_options.keys())[:6],
                format_func=lambda x: kpi_options[x],
                key="heatmap_kpis"
            )
            normalize_heat = st.checkbox("Normalizza valori", value=True, key="heat_norm")

        if heatmap_kpis:
            fig = charts.heatmap_comparison(selected_distretti, heatmap_kpis, normalize=normalize_heat)
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_x = st.selectbox(
                "KPI Asse X",
                options=list(kpi_options.keys()),
                format_func=lambda x: kpi_options[x],
                index=2,  # fatturato
                key="scatter_x"
            )
        with col2:
            kpi_y = st.selectbox(
                "KPI Asse Y",
                options=list(kpi_options.keys()),
                format_func=lambda x: kpi_options[x],
                index=1,  # addetti
                key="scatter_y"
            )
        with col3:
            kpi_size = st.selectbox(
                "KPI Dimensione (opzionale)",
                options=["Nessuno"] + list(kpi_options.keys()),
                format_func=lambda x: "Nessuno" if x == "Nessuno" else kpi_options[x],
                key="scatter_size"
            )

        size_kpi = None if kpi_size == "Nessuno" else kpi_size
        fig = charts.scatter_correlation(selected_distretti, kpi_x, kpi_y, size_kpi)
        st.plotly_chart(fig, use_container_width=True)

    # Tabella comparativa
    st.markdown("---")
    st.subheader("📋 Tabella Comparativa Dettagliata")

    df_compare = []
    for d in selected_distretti:
        row = {"Distretto": d.get("nome")}
        for kpi_key, kpi_label in kpi_options.items():
            val = d.get("kpi", {}).get(kpi_key, 0)
            if "percentuale" in kpi_key or "yoy" in kpi_key:
                row[kpi_label] = f"{val:.1f}%"
            elif val >= 1000:
                row[kpi_label] = f"{val:,.0f}"
            else:
                row[kpi_label] = f"{val:.1f}"
        df_compare.append(row)

    st.dataframe(pd.DataFrame(df_compare), use_container_width=True, hide_index=True)


# === PAGINA: DETTAGLIO DISTRETTO ===
def pagina_dettaglio():
    st.title("🔍 Dettaglio Distretto")

    distretti = dm.get_all_distretti()

    if not distretti:
        st.warning("Nessun distretto presente.")
        return

    # Selezione distretto
    nomi_distretti = {d.get("nome"): d.get("id") for d in distretti}
    selected_name = st.selectbox(
        "🏭 Seleziona Distretto",
        options=list(nomi_distretti.keys())
    )

    distretto = dm.get_distretto(nomi_distretti[selected_name])

    if not distretto:
        st.error("Distretto non trovato.")
        return

    kpi = distretto.get("kpi", {})

    # Header con info principali
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header(distretto.get("nome", "N/D"))
        st.markdown(f"**Settore:** {distretto.get('settore', 'N/D')}")
        st.markdown(f"**Provincia:** {distretto.get('provincia', 'N/D')}")
        st.markdown(f"**Comuni principali:** {', '.join(distretto.get('comuni_principali', []))}")
        st.markdown(f"_{distretto.get('descrizione', '')}_")

    with col2:
        # Indicatore di crescita
        crescita = kpi.get("crescita_yoy", 0)
        color = "green" if crescita > 0 else "red" if crescita < 0 else "gray"
        st.metric(
            "Crescita YoY",
            f"{crescita:+.1f}%",
            delta=f"{crescita:+.1f}%" if crescita != 0 else None
        )

    st.markdown("---")

    # KPI principali
    st.subheader("📊 KPI Principali")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏢 Imprese", f"{kpi.get('num_imprese', 0):,}")
    with col2:
        st.metric("👥 Addetti", f"{kpi.get('addetti', 0):,}")
    with col3:
        st.metric("💰 Fatturato", f"€{kpi.get('fatturato_mln', 0):,.0f}M")
    with col4:
        st.metric("🌍 Export", f"€{kpi.get('export_mln', 0):,.0f}M ({kpi.get('export_percentuale', 0):.1f}%)")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔬 R&D", f"€{kpi.get('investimenti_rd_mln', 0):,.0f}M")
    with col2:
        st.metric("📈 Produttività", f"€{kpi.get('produttivita', 0):,.0f}k/addetto")
    with col3:
        st.metric("🇮🇹 Quota Nazionale", f"{kpi.get('quota_mercato_nazionale', 0):.1f}%")
    with col4:
        st.metric("📊 Crescita", f"{kpi.get('crescita_yoy', 0):+.1f}%")

    st.markdown("---")

    # Trend storico
    kpi_annuali = distretto.get("kpi_annuali", {})
    if kpi_annuali:
        st.subheader("📈 Trend Storico")

        col1, col2 = st.columns([3, 1])
        with col2:
            trend_kpi = st.selectbox(
                "KPI da visualizzare",
                options=["fatturato_mln", "addetti", "export_mln"],
                format_func=lambda x: {"fatturato_mln": "Fatturato", "addetti": "Addetti", "export_mln": "Export"}[x]
            )

        # Costruisci dati trend
        anni = sorted(kpi_annuali.keys())
        valori = [kpi_annuali[a].get(trend_kpi, 0) for a in anni]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=anni,
            y=valori,
            mode='lines+markers',
            line=dict(color='#667eea', width=3),
            marker=dict(size=10),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.2)'
        ))
        fig.update_layout(
            title=f"Trend {trend_kpi.replace('_', ' ').title()}",
            xaxis_title="Anno",
            yaxis_title="Valore",
            template="plotly_white",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    # Confronto con benchmark
    st.markdown("---")
    st.subheader("📊 Confronto con Benchmark")

    settore = distretto.get("settore")
    bench_naz = dm.get_benchmark("nazionali").get(settore, {})
    bench_eur = dm.get_benchmark("europei").get(settore, {})

    if bench_naz or bench_eur:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Distretto**")
            st.write(f"Produttività: {kpi.get('produttivita', 0):.0f}")
            st.write(f"Export %: {kpi.get('export_percentuale', 0):.1f}%")
            st.write(f"Crescita: {kpi.get('crescita_yoy', 0):+.1f}%")

        with col2:
            st.markdown("**Benchmark Italia**")
            st.write(f"Produttività: {bench_naz.get('produttivita', 'N/D')}")
            st.write(f"Export %: {bench_naz.get('export_percentuale', 'N/D')}%")
            st.write(f"Crescita media: {bench_naz.get('crescita_media', 'N/D')}%")

        with col3:
            st.markdown(f"**Benchmark EU** ({bench_eur.get('riferimento', 'N/D')})")
            st.write(f"Produttività: {bench_eur.get('produttivita', 'N/D')}")
            st.write(f"Export %: {bench_eur.get('export_percentuale', 'N/D')}%")
            st.write(f"Crescita media: {bench_eur.get('crescita_media', 'N/D')}%")

    # SWOT
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ Punti di Forza")
        for punto in distretto.get("punti_forza", []):
            st.markdown(f"• {punto}")

    with col2:
        st.subheader("⚠️ Criticità")
        for punto in distretto.get("criticita", []):
            st.markdown(f"• {punto}")


# === PAGINA: GESTIONE DATI ===
def pagina_gestione():
    st.title("✏️ Gestione Dati")
    st.markdown("Aggiungi, modifica o elimina distretti e i loro KPI.")

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Modifica Distretto", "➕ Nuovo Distretto", "🗑️ Elimina", "📤 Import/Export"])

    with tab1:
        st.subheader("Modifica Distretto Esistente")

        distretti = dm.get_all_distretti()
        if not distretti:
            st.info("Nessun distretto da modificare.")
        else:
            nomi_distretti = {d.get("nome"): d.get("id") for d in distretti}
            selected_name = st.selectbox(
                "Seleziona distretto da modificare",
                options=list(nomi_distretti.keys()),
                key="edit_select"
            )

            distretto = dm.get_distretto(nomi_distretti[selected_name])

            if distretto:
                with st.form("edit_form"):
                    st.markdown("**Informazioni Generali**")

                    col1, col2 = st.columns(2)
                    with col1:
                        nome = st.text_input("Nome", value=distretto.get("nome", ""))
                        settore = st.text_input("Settore", value=distretto.get("settore", ""))
                        provincia = st.text_input("Provincia", value=distretto.get("provincia", ""))
                    with col2:
                        comuni = st.text_area(
                            "Comuni principali (uno per riga)",
                            value="\n".join(distretto.get("comuni_principali", []))
                        )
                        descrizione = st.text_area("Descrizione", value=distretto.get("descrizione", ""))

                    st.markdown("---")
                    st.markdown("**KPI**")

                    kpi = distretto.get("kpi", {})

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        num_imprese = st.number_input("Numero Imprese", value=kpi.get("num_imprese", 0), min_value=0)
                        addetti = st.number_input("Addetti", value=kpi.get("addetti", 0), min_value=0)
                    with col2:
                        fatturato = st.number_input("Fatturato (M€)", value=float(kpi.get("fatturato_mln", 0)), min_value=0.0)
                        export = st.number_input("Export (M€)", value=float(kpi.get("export_mln", 0)), min_value=0.0)
                    with col3:
                        export_pct = st.number_input("Export %", value=float(kpi.get("export_percentuale", 0)), min_value=0.0, max_value=100.0)
                        rd = st.number_input("R&D (M€)", value=float(kpi.get("investimenti_rd_mln", 0)), min_value=0.0)
                    with col4:
                        produttivita = st.number_input("Produttività", value=float(kpi.get("produttivita", 0)), min_value=0.0)
                        crescita = st.number_input("Crescita YoY %", value=float(kpi.get("crescita_yoy", 0)), min_value=-100.0, max_value=100.0)
                        quota = st.number_input("Quota Mercato Naz. %", value=float(kpi.get("quota_mercato_nazionale", 0)), min_value=0.0, max_value=100.0)

                    st.markdown("---")
                    st.markdown("**SWOT**")

                    col1, col2 = st.columns(2)
                    with col1:
                        punti_forza = st.text_area(
                            "Punti di Forza (uno per riga)",
                            value="\n".join(distretto.get("punti_forza", []))
                        )
                    with col2:
                        criticita = st.text_area(
                            "Criticità (uno per riga)",
                            value="\n".join(distretto.get("criticita", []))
                        )

                    submitted = st.form_submit_button("💾 Salva Modifiche", type="primary")

                    if submitted:
                        updated = {
                            "nome": nome,
                            "settore": settore,
                            "provincia": provincia,
                            "comuni_principali": [c.strip() for c in comuni.split("\n") if c.strip()],
                            "descrizione": descrizione,
                            "kpi": {
                                "num_imprese": num_imprese,
                                "addetti": addetti,
                                "fatturato_mln": fatturato,
                                "export_mln": export,
                                "export_percentuale": export_pct,
                                "investimenti_rd_mln": rd,
                                "produttivita": produttivita,
                                "crescita_yoy": crescita,
                                "quota_mercato_nazionale": quota
                            },
                            "punti_forza": [p.strip() for p in punti_forza.split("\n") if p.strip()],
                            "criticita": [c.strip() for c in criticita.split("\n") if c.strip()],
                            "kpi_annuali": distretto.get("kpi_annuali", {})
                        }

                        if dm.update_distretto(distretto["id"], updated):
                            st.success("✅ Distretto aggiornato con successo!")
                            st.cache_resource.clear()
                            st.rerun()
                        else:
                            st.error("❌ Errore durante l'aggiornamento.")

    with tab2:
        st.subheader("Aggiungi Nuovo Distretto")

        with st.form("new_form"):
            st.markdown("**Informazioni Generali**")

            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome", key="new_nome")
                settore = st.text_input("Settore", key="new_settore")
                provincia = st.text_input("Provincia", key="new_provincia")
            with col2:
                comuni = st.text_area("Comuni principali (uno per riga)", key="new_comuni")
                descrizione = st.text_area("Descrizione", key="new_desc")

            st.markdown("---")
            st.markdown("**KPI**")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                num_imprese = st.number_input("Numero Imprese", value=0, min_value=0, key="new_imprese")
                addetti = st.number_input("Addetti", value=0, min_value=0, key="new_addetti")
            with col2:
                fatturato = st.number_input("Fatturato (M€)", value=0.0, min_value=0.0, key="new_fatt")
                export = st.number_input("Export (M€)", value=0.0, min_value=0.0, key="new_export")
            with col3:
                export_pct = st.number_input("Export %", value=0.0, min_value=0.0, max_value=100.0, key="new_exp_pct")
                rd = st.number_input("R&D (M€)", value=0.0, min_value=0.0, key="new_rd")
            with col4:
                produttivita = st.number_input("Produttività", value=0.0, min_value=0.0, key="new_prod")
                crescita = st.number_input("Crescita YoY %", value=0.0, min_value=-100.0, max_value=100.0, key="new_crescita")
                quota = st.number_input("Quota Mercato Naz. %", value=0.0, min_value=0.0, max_value=100.0, key="new_quota")

            submitted = st.form_submit_button("➕ Aggiungi Distretto", type="primary")

            if submitted:
                if not nome or not settore:
                    st.error("Nome e Settore sono obbligatori.")
                else:
                    new_distretto = {
                        "nome": nome,
                        "settore": settore,
                        "provincia": provincia,
                        "comuni_principali": [c.strip() for c in comuni.split("\n") if c.strip()],
                        "descrizione": descrizione,
                        "kpi": {
                            "num_imprese": num_imprese,
                            "addetti": addetti,
                            "fatturato_mln": fatturato,
                            "export_mln": export,
                            "export_percentuale": export_pct,
                            "investimenti_rd_mln": rd,
                            "produttivita": produttivita,
                            "crescita_yoy": crescita,
                            "quota_mercato_nazionale": quota
                        },
                        "punti_forza": [],
                        "criticita": [],
                        "kpi_annuali": {}
                    }

                    if dm.add_distretto(new_distretto):
                        st.success("✅ Distretto aggiunto con successo!")
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("❌ Errore durante l'aggiunta.")

    with tab3:
        st.subheader("Elimina Distretto")

        distretti = dm.get_all_distretti()
        if not distretti:
            st.info("Nessun distretto da eliminare.")
        else:
            nomi_distretti = {d.get("nome"): d.get("id") for d in distretti}
            selected_name = st.selectbox(
                "Seleziona distretto da eliminare",
                options=list(nomi_distretti.keys()),
                key="del_select"
            )

            st.warning(f"⚠️ Stai per eliminare **{selected_name}**. Questa azione è irreversibile!")

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Elimina", type="primary"):
                    if dm.delete_distretto(nomi_distretti[selected_name]):
                        st.success("✅ Distretto eliminato!")
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("❌ Errore durante l'eliminazione.")

    with tab4:
        st.subheader("Import/Export Dati")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📥 Esporta Dati**")
            if st.button("Scarica backup completo"):
                import json
                distretti_data = dm._load_json(dm.distretti_file)
                benchmark_data = dm._load_json(dm.benchmark_file)

                export_data = {
                    "distretti": distretti_data,
                    "benchmark": benchmark_data
                }

                st.download_button(
                    label="💾 Download JSON",
                    data=json.dumps(export_data, indent=2, ensure_ascii=False),
                    file_name="distretti_backup.json",
                    mime="application/json"
                )

        with col2:
            st.markdown("**📤 Importa Dati**")
            uploaded = st.file_uploader("Carica file JSON", type=["json"])

            if uploaded:
                import json
                try:
                    data = json.load(uploaded)
                    st.json(data)

                    if st.button("✅ Conferma Import"):
                        if dm.import_data(uploaded.name):
                            st.success("Dati importati!")
                            st.cache_resource.clear()
                            st.rerun()
                except Exception as e:
                    st.error(f"Errore nel file: {e}")


# === PAGINA: STORICO MODIFICHE ===
def pagina_storico():
    st.title("📜 Storico Modifiche")
    st.markdown("Registro delle modifiche effettuate ai dati.")

    storico = dm.get_storico(limit=100)

    if not storico:
        st.info("Nessuna modifica registrata.")
        return

    # Filtri
    col1, col2 = st.columns(2)
    with col1:
        azioni = list(set(s.get("azione") for s in storico))
        filtro_azione = st.multiselect("Filtra per azione", options=azioni, default=azioni)

    # Tabella storico
    df_storico = []
    for entry in storico:
        if entry.get("azione") in filtro_azione:
            df_storico.append({
                "Data/Ora": entry.get("timestamp", "")[:19].replace("T", " "),
                "Azione": entry.get("azione", "").upper(),
                "Distretto ID": entry.get("distretto_id", "N/D"),
                "Dettagli": str(entry.get("dati", {}))[:100] + "..."
            })

    if df_storico:
        st.dataframe(pd.DataFrame(df_storico), use_container_width=True, hide_index=True)
    else:
        st.info("Nessun risultato con i filtri selezionati.")


# === ROUTING PAGINE ===
if "🏠 Dashboard" in pagina:
    pagina_dashboard()
elif "📊 Confronta" in pagina:
    pagina_confronto()
elif "🔍 Dettaglio" in pagina:
    pagina_dettaglio()
elif "✏️ Gestione" in pagina:
    pagina_gestione()
elif "📜 Storico" in pagina:
    pagina_storico()
