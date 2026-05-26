# core/database.py
import os
import json
import csv
import shutil
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Material:
    total: int
    available: int
    
    @property
    def missing(self) -> int: 
        return max(0, self.total - self.available)

class DataManager:
    META_KEY = "__IGNORED_METADATA__"

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.backup_path = f"{filepath}.bak" if filepath else None
        self.data: Dict[str, Dict[str, Material]] = {}
        self.ignored_categories: Dict[str, str] = {}
        self._last_imported_names: List[str] = []
        self.load_data()

    def set_filepath(self, new_filepath: str):
        self.filepath = new_filepath
        self.backup_path = f"{new_filepath}.bak" if new_filepath else None
        self.load_data()

    def load_data(self):
        if not self.filepath or not os.path.exists(self.filepath):
            self.data, self.ignored_categories = {}, {}
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f: 
                raw_data = json.load(f)
            self.ignored_categories = raw_data.pop(self.META_KEY) if self.META_KEY in raw_data else {}
            self.data = {cat: {name: Material(**props) for name, props in items.items()} for cat, items in raw_data.items()}
        except (json.JSONDecodeError, TypeError): 
            self.data, self.ignored_categories = {}, {}

    def save_data(self) -> bool:
        if not self.filepath: return False
        if os.path.exists(self.filepath):
            try: shutil.copy(self.filepath, self.backup_path)
            except IOError: pass 
            
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                data_to_save = {cat: {name: asdict(mat) for name, mat in items.items()} for cat, items in self.data.items()}
                if self.ignored_categories: 
                    data_to_save[self.META_KEY] = self.ignored_categories
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            return True
        except IOError: 
            return False

    def toggle_ignore_category(self, category: str):
        if category in self.ignored_categories: 
            del self.ignored_categories[category]
        else: 
            self.ignored_categories[category] = datetime.now().strftime("%d/%m/%Y - %H:%M")

    def is_ignored(self, category: str) -> bool: return category in self.ignored_categories
    def get_ignore_timestamp(self, category: str) -> str: return self.ignored_categories.get(category, "")
    def get_all_categories(self) -> List[str]: return sorted(list(self.data.keys()))

    def export_to_csv(self, filepath: str) -> bool:
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Categoria Principale', 'Sottocategoria', 'Materiale', 'Totale Richiesto', 'Disponibile', 'Mancante', 'Stato'])
                for category, items in self.data.items():
                    main_c, sub_c = category.split(" // ", 1) if " // " in category else (category, "Generale")
                    status = f"Ignorato ({self.ignored_categories[category]})" if category in self.ignored_categories else "Attivo"
                    for name, mat in items.items(): 
                        writer.writerow([main_c, sub_c, name, mat.total, mat.available, mat.missing, status])
            return True
        except IOError: 
            return False

    def _parse_lines(self, lines: list, category_name: str) -> int:
        if category_name not in self.data: self.data[category_name] = {}
        parsed_count = 0
        names_found: List[str] = []
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.lower().startswith(("| item", "item", "#")): continue
            
            # 1. Parsing avanzato per tabelle Litematica (es: | air | 0 | oppure | Stone | 150 |)
            if "|" in line_str:
                parts = [p.strip() for p in line_str.split("|") if p.strip()]
                if len(parts) >= 2:
                    try:
                        name, num_str = parts[0], parts[1]
                        if num_str.isdigit():
                            formatted_name = name.strip().replace("minecraft:", "").replace("_", " ").title()
                            if ":" in formatted_name: formatted_name = formatted_name.split(":")[-1].title()
                            
                            if formatted_name in self.data[category_name]:
                                self.data[category_name][formatted_name].total = int(num_str)
                            else:
                                self.data[category_name][formatted_name] = Material(total=int(num_str), available=0)
                            parsed_count += 1
                            names_found.append(formatted_name)
                            continue
                    except ValueError: pass

            # 2. Parsing standard tollerante (es: "50x Stone" o "Stone: 64")
            match = re.search(r'(?:(\d+)\s*x\s*)?([a-zA-Z0-9_\-:]+(?:\s+[a-zA-Z0-9_\-]+)*)[:\s\-]+(\d+)?', line_str)
            if match:
                g1, g2, g3 = match.group(1), match.group(2), match.group(3)
                final_count = int(g1) if g1 else (int(g3) if g3 and g3.isdigit() else None)
                if final_count is not None and g2:
                    if g2.lower() in ("item", "total", "missing"): continue
                    formatted_name = g2.strip().replace("minecraft:", "").replace("_", " ").title()
                    if ":" in formatted_name: formatted_name = formatted_name.split(":")[-1].title()
                    
                    if formatted_name in self.data[category_name]:
                        self.data[category_name][formatted_name].total = final_count
                    else:
                        self.data[category_name][formatted_name] = Material(total=final_count, available=0)
                    parsed_count += 1
                    names_found.append(formatted_name)

        self._last_imported_names = names_found
        return parsed_count

    def import_from_txt(self, filepath: str, category_name: str) -> int:
        try:
            with open(filepath, 'r', encoding='utf-8') as f: 
                return self._parse_lines(f.readlines(), category_name)
        except Exception: return -1

    def import_from_string(self, text_content: str, category_name: str) -> int:
        return self._parse_lines(text_content.splitlines(), category_name)
 
    def import_from_json(self, filepath: str, category_name: str) -> int:
        """Importa direttamente i dati dal file JSON (Litematica) senza scomposizione in risorse grezze."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f: 
                data = json.load(f)
            
            if category_name not in self.data: 
                self.data[category_name] = {}
                
            parsed_count = 0
            names_found: List[str] = []
            
            # Normalizza i dati se non sono all'interno di una lista
            lista_elementi = data if isinstance(data, list) else [data]
            
            for item in lista_elementi:
                if not isinstance(item, dict): continue
                # Cerca chiavi comuni usate dai formati di Litematica o personalizzati
                raw_item = item.get("RawItem", item.get("Item", item.get("id", item.get("name"))))
                total = item.get("TotalEstimate", item.get("total", item.get("count", item.get("Count"))))
                
                if raw_item and total is not None:
                    name = str(raw_item).replace("minecraft:", "").replace("_", " ").title()
                    if ":" in name: name = name.split(":")[-1].title()
                    
                    try:
                        final_qty = int(total)
                        if name in self.data[category_name]: 
                            self.data[category_name][name].total += final_qty
                        else: 
                            self.data[category_name][name] = Material(total=final_qty, available=0)
                        parsed_count += 1
                        names_found.append(name)
                    except (ValueError, TypeError): pass
                    
            self._last_imported_names = names_found
            return parsed_count
        except Exception:
            self._last_imported_names = []
            return -1