"""
Modulo per la creazione di grafici interattivi con Plotly.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Optional
import numpy as np


class ChartManager:
    """Gestisce la creazione di grafici interattivi per il comparatore."""

    # Palette colori per i distretti
    COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
    ]

    @staticmethod
    def bar_comparison(distretti: List[Dict], kpi: str, title: str = None,
                       show_benchmark: bool = False, benchmark_value: float = None) -> go.Figure:
        """
        Crea un grafico a barre per confrontare un KPI tra distretti.

        Args:
            distretti: Lista di dizionari dei distretti
            kpi: Nome del KPI da confrontare
            title: Titolo del grafico
            show_benchmark: Se mostrare la linea benchmark
            benchmark_value: Valore del benchmark
        """
        if not distretti:
            return go.Figure()

        nomi = [d.get("nome", d.get("id", "N/D")) for d in distretti]
        valori = [d.get("kpi", {}).get(kpi, 0) for d in distretti]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=nomi,
            y=valori,
            marker_color=ChartManager.COLORS[:len(distretti)],
            text=[f"{v:,.0f}" if v >= 1 else f"{v:.2f}" for v in valori],
            textposition='outside',
            hovertemplate="<b>%{x}</b><br>" + f"{kpi}: " + "%{y:,.2f}<extra></extra>"
        ))

        if show_benchmark and benchmark_value is not None:
            fig.add_hline(
                y=benchmark_value,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Benchmark: {benchmark_value:,.2f}",
                annotation_position="top right"
            )

        fig.update_layout(
            title=title or f"Confronto {kpi}",
            xaxis_title="Distretto",
            yaxis_title=kpi,
            template="plotly_white",
            showlegend=False,
            height=450
        )

        return fig

    @staticmethod
    def radar_comparison(distretti: List[Dict], kpi_list: List[str],
                         normalize: bool = True) -> go.Figure:
        """
        Crea un grafico radar per confrontare più KPI tra distretti.

        Args:
            distretti: Lista di dizionari dei distretti
            kpi_list: Lista dei KPI da confrontare
            normalize: Se normalizzare i valori (0-100)
        """
        if not distretti or not kpi_list:
            return go.Figure()

        fig = go.Figure()

        # Calcola valori normalizzati se richiesto
        all_values = {kpi: [] for kpi in kpi_list}
        for d in distretti:
            for kpi in kpi_list:
                val = d.get("kpi", {}).get(kpi, 0)
                all_values[kpi].append(val)

        # Trova min/max per normalizzazione
        ranges = {}
        for kpi in kpi_list:
            vals = all_values[kpi]
            ranges[kpi] = (min(vals) if vals else 0, max(vals) if vals else 1)

        for i, d in enumerate(distretti):
            values = []
            for kpi in kpi_list:
                val = d.get("kpi", {}).get(kpi, 0)
                if normalize:
                    min_v, max_v = ranges[kpi]
                    if max_v - min_v > 0:
                        val = ((val - min_v) / (max_v - min_v)) * 100
                    else:
                        val = 50
                values.append(val)

            # Chiudi il poligono
            values.append(values[0])
            kpi_labels = kpi_list + [kpi_list[0]]

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=kpi_labels,
                fill='toself',
                name=d.get("nome", d.get("id", f"Distretto {i+1}")),
                line_color=ChartManager.COLORS[i % len(ChartManager.COLORS)],
                opacity=0.7
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100] if normalize else None
                )
            ),
            showlegend=True,
            title="Confronto Multi-KPI (Radar)",
            template="plotly_white",
            height=500
        )

        return fig

    @staticmethod
    def trend_line(distretti: List[Dict], kpi: str, anni: List[int] = None) -> go.Figure:
        """
        Crea un grafico a linee per mostrare il trend di un KPI nel tempo.

        Args:
            distretti: Lista di dizionari dei distretti
            kpi: Nome del KPI
            anni: Lista degli anni da mostrare
        """
        if not distretti:
            return go.Figure()

        fig = go.Figure()

        for i, d in enumerate(distretti):
            kpi_annuali = d.get("kpi_annuali", {})

            if not kpi_annuali:
                continue

            anni_data = sorted(kpi_annuali.keys())
            if anni:
                anni_data = [a for a in anni_data if int(a) in anni]

            valori = [kpi_annuali.get(a, {}).get(kpi, None) for a in anni_data]

            fig.add_trace(go.Scatter(
                x=anni_data,
                y=valori,
                mode='lines+markers',
                name=d.get("nome", d.get("id", f"Distretto {i+1}")),
                line=dict(color=ChartManager.COLORS[i % len(ChartManager.COLORS)], width=2),
                marker=dict(size=8),
                hovertemplate="<b>%{x}</b><br>" + f"{kpi}: %{{y:,.2f}}<extra></extra>"
            ))

        fig.update_layout(
            title=f"Trend {kpi} nel tempo",
            xaxis_title="Anno",
            yaxis_title=kpi,
            template="plotly_white",
            hovermode="x unified",
            height=450
        )

        return fig

    @staticmethod
    def scatter_correlation(distretti: List[Dict], kpi_x: str, kpi_y: str,
                            size_kpi: str = None) -> go.Figure:
        """
        Crea un grafico scatter per visualizzare correlazione tra due KPI.

        Args:
            distretti: Lista di dizionari dei distretti
            kpi_x: KPI per asse X
            kpi_y: KPI per asse Y
            size_kpi: KPI per dimensione bolle (opzionale)
        """
        if not distretti:
            return go.Figure()

        nomi = [d.get("nome", d.get("id", "N/D")) for d in distretti]
        x_values = [d.get("kpi", {}).get(kpi_x, 0) for d in distretti]
        y_values = [d.get("kpi", {}).get(kpi_y, 0) for d in distretti]

        if size_kpi:
            size_values = [d.get("kpi", {}).get(size_kpi, 10) for d in distretti]
            # Normalizza dimensioni
            max_size = max(size_values) if size_values else 1
            sizes = [max(10, (s / max_size) * 50) for s in size_values]
        else:
            sizes = [20] * len(distretti)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='markers+text',
            text=nomi,
            textposition="top center",
            marker=dict(
                size=sizes,
                color=ChartManager.COLORS[:len(distretti)],
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            hovertemplate="<b>%{text}</b><br>" +
                          f"{kpi_x}: %{{x:,.2f}}<br>" +
                          f"{kpi_y}: %{{y:,.2f}}<extra></extra>"
        ))

        fig.update_layout(
            title=f"Correlazione {kpi_x} vs {kpi_y}",
            xaxis_title=kpi_x,
            yaxis_title=kpi_y,
            template="plotly_white",
            height=500
        )

        return fig

    @staticmethod
    def pie_distribution(distretti: List[Dict], kpi: str, title: str = None) -> go.Figure:
        """
        Crea un grafico a torta per mostrare distribuzione di un KPI.
        """
        if not distretti:
            return go.Figure()

        nomi = [d.get("nome", d.get("id", "N/D")) for d in distretti]
        valori = [d.get("kpi", {}).get(kpi, 0) for d in distretti]

        fig = go.Figure(data=[go.Pie(
            labels=nomi,
            values=valori,
            hole=0.4,
            marker_colors=ChartManager.COLORS[:len(distretti)],
            textinfo='label+percent',
            hovertemplate="<b>%{label}</b><br>" +
                          f"{kpi}: %{{value:,.0f}}<br>" +
                          "Quota: %{percent}<extra></extra>"
        )])

        fig.update_layout(
            title=title or f"Distribuzione {kpi}",
            template="plotly_white",
            height=450
        )

        return fig

    @staticmethod
    def grouped_bar(distretti: List[Dict], kpi_list: List[str]) -> go.Figure:
        """
        Crea un grafico a barre raggruppate per più KPI.
        """
        if not distretti or not kpi_list:
            return go.Figure()

        fig = go.Figure()

        nomi = [d.get("nome", d.get("id", "N/D")) for d in distretti]

        for i, kpi in enumerate(kpi_list):
            valori = [d.get("kpi", {}).get(kpi, 0) for d in distretti]

            fig.add_trace(go.Bar(
                name=kpi,
                x=nomi,
                y=valori,
                marker_color=ChartManager.COLORS[i % len(ChartManager.COLORS)],
                text=[f"{v:,.0f}" if v >= 1 else f"{v:.2f}" for v in valori],
                textposition='outside'
            ))

        fig.update_layout(
            barmode='group',
            title="Confronto Multi-KPI",
            xaxis_title="Distretto",
            yaxis_title="Valore",
            template="plotly_white",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

    @staticmethod
    def heatmap_comparison(distretti: List[Dict], kpi_list: List[str],
                           normalize: bool = True) -> go.Figure:
        """
        Crea una heatmap per confrontare distretti su più KPI.
        """
        if not distretti or not kpi_list:
            return go.Figure()

        nomi = [d.get("nome", d.get("id", "N/D")) for d in distretti]

        # Costruisci matrice
        data = []
        for d in distretti:
            row = [d.get("kpi", {}).get(kpi, 0) for kpi in kpi_list]
            data.append(row)

        df = pd.DataFrame(data, index=nomi, columns=kpi_list)

        # Normalizza per colonna se richiesto
        if normalize:
            df = (df - df.min()) / (df.max() - df.min()) * 100
            df = df.fillna(0)

        fig = go.Figure(data=go.Heatmap(
            z=df.values,
            x=kpi_list,
            y=nomi,
            colorscale='RdYlGn',
            text=[[f"{v:.1f}" for v in row] for row in df.values],
            texttemplate="%{text}",
            hovertemplate="<b>%{y}</b><br>" +
                          "%{x}: %{z:.1f}<extra></extra>"
        ))

        fig.update_layout(
            title="Heatmap Confronto KPI" + (" (normalizzato)" if normalize else ""),
            xaxis_title="KPI",
            yaxis_title="Distretto",
            template="plotly_white",
            height=400 + len(distretti) * 30
        )

        return fig

    @staticmethod
    def summary_cards_data(distretti: List[Dict]) -> Dict:
        """
        Calcola i dati per le card di riepilogo.

        Returns:
            Dict con statistiche aggregate
        """
        if not distretti:
            return {}

        totale_imprese = sum(d.get("kpi", {}).get("num_imprese", 0) for d in distretti)
        totale_addetti = sum(d.get("kpi", {}).get("addetti", 0) for d in distretti)
        totale_fatturato = sum(d.get("kpi", {}).get("fatturato_mln", 0) for d in distretti)
        totale_export = sum(d.get("kpi", {}).get("export_mln", 0) for d in distretti)

        avg_produttivita = np.mean([
            d.get("kpi", {}).get("produttivita", 0) for d in distretti
            if d.get("kpi", {}).get("produttivita", 0) > 0
        ]) if distretti else 0

        avg_export_pct = np.mean([
            d.get("kpi", {}).get("export_percentuale", 0) for d in distretti
            if d.get("kpi", {}).get("export_percentuale", 0) > 0
        ]) if distretti else 0

        return {
            "totale_imprese": totale_imprese,
            "totale_addetti": totale_addetti,
            "totale_fatturato": totale_fatturato,
            "totale_export": totale_export,
            "media_produttivita": avg_produttivita,
            "media_export_pct": avg_export_pct,
            "num_distretti": len(distretti)
        }
