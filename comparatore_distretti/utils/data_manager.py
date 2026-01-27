"""
Modulo per la gestione dei dati dei distretti industriali.
Gestisce caricamento, salvataggio e modifica con persistenza JSON.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class DataManager:
    """Gestisce i dati dei distretti industriali con persistenza JSON."""

    def __init__(self, data_dir: str = None):
        """
        Inizializza il DataManager.

        Args:
            data_dir: Directory dove salvare i file JSON. Se None, usa ./data
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.distretti_file = self.data_dir / "distretti.json"
        self.benchmark_file = self.data_dir / "benchmark.json"
        self.storico_file = self.data_dir / "storico.json"

        # Inizializza i file se non esistono
        self._init_files()

    def _init_files(self):
        """Inizializza i file JSON se non esistono."""
        if not self.distretti_file.exists():
            self._save_json(self.distretti_file, {"distretti": [], "ultimo_aggiornamento": None})
        if not self.benchmark_file.exists():
            self._save_json(self.benchmark_file, {"benchmark_nazionali": {}, "benchmark_europei": {}})
        if not self.storico_file.exists():
            self._save_json(self.storico_file, {"storico": []})

    def _load_json(self, filepath: Path) -> Dict:
        """Carica un file JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_json(self, filepath: Path, data: Dict) -> bool:
        """Salva dati in un file JSON."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Errore salvataggio {filepath}: {e}")
            return False

    # === GESTIONE DISTRETTI ===

    def get_all_distretti(self) -> List[Dict]:
        """Restituisce tutti i distretti."""
        data = self._load_json(self.distretti_file)
        return data.get("distretti", [])

    def get_distretto(self, distretto_id: str) -> Optional[Dict]:
        """Restituisce un singolo distretto per ID."""
        distretti = self.get_all_distretti()
        for d in distretti:
            if d.get("id") == distretto_id:
                return d
        return None

    def get_distretti_by_ids(self, ids: List[str]) -> List[Dict]:
        """Restituisce più distretti per lista di ID."""
        distretti = self.get_all_distretti()
        return [d for d in distretti if d.get("id") in ids]

    def add_distretto(self, distretto: Dict) -> bool:
        """Aggiunge un nuovo distretto."""
        data = self._load_json(self.distretti_file)

        # Genera ID se non presente
        if "id" not in distretto:
            distretto["id"] = self._generate_id(distretto.get("nome", "distretto"))

        # Controlla se esiste già
        existing_ids = [d.get("id") for d in data.get("distretti", [])]
        if distretto["id"] in existing_ids:
            return False

        distretto["data_creazione"] = datetime.now().isoformat()
        distretto["data_modifica"] = datetime.now().isoformat()

        data.setdefault("distretti", []).append(distretto)
        data["ultimo_aggiornamento"] = datetime.now().isoformat()

        # Salva nello storico
        self._add_to_storico("add", distretto["id"], distretto)

        return self._save_json(self.distretti_file, data)

    def update_distretto(self, distretto_id: str, updates: Dict) -> bool:
        """Aggiorna un distretto esistente."""
        data = self._load_json(self.distretti_file)

        for i, d in enumerate(data.get("distretti", [])):
            if d.get("id") == distretto_id:
                # Preserva ID e data creazione
                updates["id"] = distretto_id
                updates["data_creazione"] = d.get("data_creazione")
                updates["data_modifica"] = datetime.now().isoformat()

                data["distretti"][i] = {**d, **updates}
                data["ultimo_aggiornamento"] = datetime.now().isoformat()

                # Salva nello storico
                self._add_to_storico("update", distretto_id, updates)

                return self._save_json(self.distretti_file, data)

        return False

    def delete_distretto(self, distretto_id: str) -> bool:
        """Elimina un distretto."""
        data = self._load_json(self.distretti_file)

        original_len = len(data.get("distretti", []))
        data["distretti"] = [d for d in data.get("distretti", []) if d.get("id") != distretto_id]

        if len(data["distretti"]) < original_len:
            data["ultimo_aggiornamento"] = datetime.now().isoformat()
            self._add_to_storico("delete", distretto_id, {})
            return self._save_json(self.distretti_file, data)

        return False

    # === GESTIONE KPI ===

    def update_kpi(self, distretto_id: str, anno: int, kpi: Dict) -> bool:
        """Aggiorna i KPI di un distretto per un anno specifico."""
        distretto = self.get_distretto(distretto_id)
        if not distretto:
            return False

        if "kpi_annuali" not in distretto:
            distretto["kpi_annuali"] = {}

        distretto["kpi_annuali"][str(anno)] = kpi

        return self.update_distretto(distretto_id, distretto)

    def get_kpi_comparison(self, distretto_ids: List[str], kpi_names: List[str], anno: int = None) -> Dict:
        """
        Restituisce i KPI per confronto tra distretti.

        Returns:
            Dict con struttura {kpi_name: {distretto_id: valore}}
        """
        distretti = self.get_distretti_by_ids(distretto_ids)

        result = {kpi: {} for kpi in kpi_names}

        for d in distretti:
            d_id = d.get("id")
            kpi_data = d.get("kpi", {})

            # Se specificato un anno, usa i dati annuali
            if anno and "kpi_annuali" in d:
                kpi_data = d["kpi_annuali"].get(str(anno), kpi_data)

            for kpi in kpi_names:
                if kpi in kpi_data:
                    result[kpi][d_id] = kpi_data[kpi]

        return result

    # === GESTIONE BENCHMARK ===

    def get_benchmark(self, tipo: str = "nazionali") -> Dict:
        """Restituisce i benchmark (nazionali o europei)."""
        data = self._load_json(self.benchmark_file)
        key = f"benchmark_{tipo}"
        return data.get(key, {})

    def update_benchmark(self, tipo: str, settore: str, valori: Dict) -> bool:
        """Aggiorna i benchmark per un settore."""
        data = self._load_json(self.benchmark_file)
        key = f"benchmark_{tipo}"

        if key not in data:
            data[key] = {}

        data[key][settore] = valori
        data["ultimo_aggiornamento"] = datetime.now().isoformat()

        return self._save_json(self.benchmark_file, data)

    # === STORICO MODIFICHE ===

    def _add_to_storico(self, azione: str, distretto_id: str, dati: Dict):
        """Aggiunge un'entry allo storico modifiche."""
        data = self._load_json(self.storico_file)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "azione": azione,
            "distretto_id": distretto_id,
            "dati": dati
        }

        data.setdefault("storico", []).append(entry)

        # Mantieni solo le ultime 1000 modifiche
        if len(data["storico"]) > 1000:
            data["storico"] = data["storico"][-1000:]

        self._save_json(self.storico_file, data)

    def get_storico(self, limit: int = 50) -> List[Dict]:
        """Restituisce lo storico delle modifiche."""
        data = self._load_json(self.storico_file)
        storico = data.get("storico", [])
        return storico[-limit:][::-1]  # Ultime N in ordine inverso

    # === UTILITY ===

    def _generate_id(self, nome: str) -> str:
        """Genera un ID univoco dal nome."""
        import re
        base_id = re.sub(r'[^a-z0-9]', '_', nome.lower())
        base_id = re.sub(r'_+', '_', base_id).strip('_')
        return f"{base_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def export_data(self, filepath: str) -> bool:
        """Esporta tutti i dati in un unico file JSON."""
        export = {
            "distretti": self._load_json(self.distretti_file),
            "benchmark": self._load_json(self.benchmark_file),
            "export_date": datetime.now().isoformat()
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def import_data(self, filepath: str) -> bool:
        """Importa dati da un file JSON esportato."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "distretti" in data:
                self._save_json(self.distretti_file, data["distretti"])
            if "benchmark" in data:
                self._save_json(self.benchmark_file, data["benchmark"])

            return True
        except Exception:
            return False

    def get_statistiche_generali(self) -> Dict:
        """Restituisce statistiche aggregate su tutti i distretti."""
        distretti = self.get_all_distretti()

        if not distretti:
            return {}

        stats = {
            "num_distretti": len(distretti),
            "settori": list(set(d.get("settore", "N/D") for d in distretti)),
            "province": list(set(d.get("provincia", "N/D") for d in distretti)),
            "totale_imprese": sum(d.get("kpi", {}).get("num_imprese", 0) for d in distretti),
            "totale_addetti": sum(d.get("kpi", {}).get("addetti", 0) for d in distretti),
            "totale_fatturato": sum(d.get("kpi", {}).get("fatturato_mln", 0) for d in distretti),
        }

        return stats
