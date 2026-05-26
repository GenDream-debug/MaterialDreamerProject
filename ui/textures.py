import sys
import os
import subprocess

# =============================================================================
# 1. AUTO-INSTALLER LIBRERIE E SETUP INIZIALE
# =============================================================================
def check_and_install_dependencies():
    """Controlla se le librerie necessarie sono presenti, altrimenti le scarica in automatico."""
    required_packages = {
        "Pillow": "PIL", 
        "tkinterdnd2": "tkinterdnd2", 
        "pywinstyles": "pywinstyles", 
        "sv-ttk": "sv_ttk",
        "litemapy": "litemapy"
    }
    missing = []
    
    for pkg, imp in required_packages.items():
        try: 
            __import__(imp)
        except ImportError: 
            missing.append(pkg)
            
    if missing:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        
        msg = f"Download componenti grafici in corso...\n\nPacchetti: {', '.join(missing)}\n\nAttendi pochi secondi."
        messagebox.showinfo("Aggiornamento", msg)
        
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + missing, creationflags=flags)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile scaricare le librerie: {e}")
            sys.exit()

# Esegue il check prima di importare il resto
check_and_install_dependencies()

# =============================================================================
# 2. IMPORTAZIONI GLOBALI
# =============================================================================
import json
import csv
import re
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

import tkinter as tk
from tkinter import simpledialog, ttk, filedialog, messagebox, Toplevel
from PIL import Image, ImageTk
from tkinterdnd2 import TkinterDnD, DND_FILES
import pywinstyles
import sv_ttk

# =============================================================================
# 3. COSTANTI GLOBALI E COLORI
# =============================================================================
GREEN = "#4cc26e"
YELLOW = "#f0b232"
RED = "#e84a5f"
TEXT_MUTED = "#8a8a8a"
BG_MAIN = "#1e1e1e"
BG_SEC = "#2b2b2b"
TEXT_MAIN = "#dbdee1"
BLURPLE = "#5865F2"

CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".material_manager_config.json")

# Pre-compilazione delle Regex per massimizzare le performance durante l'importazione
PATTERN_MATERIALE = re.compile(
    r'^([a-zA-Z_:\s]+?)[:\-]?\s+([\d\+\-\*\/\(\)\.\s]+(?:sb|stk|stack|shulker)?.*)$', 
    re.IGNORECASE
)
PATTERN_LITEMATIC_LINE = re.compile(r"\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|")

# =============================================================================
# 4. GESTIONE DELLA CONFIGURAZIONE
# =============================================================================
def load_config() -> dict:
    """Carica la configurazione utente dal file JSON."""
    if not os.path.exists(CONFIG_FILE_PATH): 
        return {}
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f: 
            return json.load(f)
    except (json.JSONDecodeError, IOError): 
        return {}

def save_config(config: dict) -> None:
    """Salva la configurazione utente."""
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f: 
            json.dump(config, f, indent=4)
    except IOError: 
        pass

# =============================================================================
# 5. COMPONENTI UI PERSONALIZZATI
# =============================================================================
class ToolTip:
    """Aggiunge un fumetto informativo al passaggio del mouse su un elemento."""
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left', background="#2b2b2b", 
                         foreground="#ffffff", relief='solid', borderwidth=1, 
                         font=("Segoe UI", 9), padx=5, pady=3)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None


def modern_messagebox(parent: tk.Widget, title: str, message: str, msg_type: str = "info"):
    """Finestra di messaggio con stile scuro coerente col programma."""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("450x180")
    dialog.transient(parent)
    dialog.grab_set()
    pywinstyles.apply_style(dialog, "dark")
    
    color = GREEN if msg_type == "success" else (RED if msg_type == "error" else "#0078d4")
    icon = "✔️" if msg_type == "success" else ("❌" if msg_type == "error" else "ℹ️")
    
    frame = ttk.Frame(dialog, padding=20)
    frame.pack(fill="both", expand=True)
    
    ttk.Label(frame, text=f"{icon} {title}", font=("Segoe UI", 12, "bold"), foreground=color).pack(anchor="w", pady=(0, 10))
    ttk.Label(frame, text=message, wraplength=400).pack(anchor="w", fill="x", expand=True)
    
    style_btn = "Accent.TButton" if msg_type != "error" else "TButton"
    btn = ttk.Button(frame, text="OK", command=dialog.destroy, style=style_btn)
    btn.pack(side="right", pady=(10, 0))
    
    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    parent.wait_window(dialog)


def modern_askyesno(parent: tk.Widget, title: str, message: str) -> bool:
    """Finestra di conferma (Sì/No) con stile scuro coerente."""
    result = [False]
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("450x180")
    dialog.transient(parent)
    dialog.grab_set()
    pywinstyles.apply_style(dialog, "dark")
    
    frame = ttk.Frame(dialog, padding=20)
    frame.pack(fill="both", expand=True)
    
    ttk.Label(frame, text=f"❓ {title}", font=("Segoe UI", 12, "bold"), foreground=YELLOW).pack(anchor="w", pady=(0, 10))
    ttk.Label(frame, text=message, wraplength=400).pack(anchor="w", fill="x", expand=True)
    
    def set_yes(): 
        result[0] = True
        dialog.destroy()
        
    def set_no(): 
        result[0] = False
        dialog.destroy()
    
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", pady=(10, 0))
    ttk.Button(btn_frame, text="Sì, Procedi", command=set_yes, style="Accent.TButton").pack(side="right", padx=(5,0))
    ttk.Button(btn_frame, text="Annulla", command=set_no).pack(side="right")
    
    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    parent.wait_window(dialog)
    return result[0]


class TextProgressBar(tk.Canvas):
    """Barra di progresso personalizzata con testo sovrapposto."""
    def __init__(self, master, height=25, bg_color="#1e1e1e", fill_color="#0078d4", text_color="#ffffff"):
        super().__init__(master, height=height, bg=bg_color, highlightthickness=0)
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.text_color = text_color
        self.value = 0
        self.max_value = 100
        self.text = ""
        self.bind("<Configure>", self._on_resize)

    def update_bar(self, current: int, total: int, text_display: str):
        self.value = current
        self.max_value = total if total > 0 else 1
        self.text = text_display
        self._draw()

    def _on_resize(self, event): 
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        fill_width = w * max(0, min(1, self.value / self.max_value if self.max_value > 0 else 0))
        self.create_rectangle(0, 0, w, h, fill=self.bg_color, width=0)
        self.create_rectangle(0, 0, fill_width, h, fill=self.fill_color, width=0)
        self.create_text(w/2, h/2, text=self.text, fill=self.text_color, font=("Segoe UI Variable Display", 10, "bold"))


# =============================================================================
# 6. LOGICA DI BUSINESS E MATEMATICA
# =============================================================================
def evaluate_math_expression(expression: str) -> int:
    """Valuta stringhe matematiche permettendo abbreviazioni come 'sb' (shulker) e 'stk' (stack)."""
    clean_expr = str(expression).lower().strip().replace("sb", "*1728").replace("stk", "*64").replace("stack", "*64")
    if not re.match(r'^[\d\+\-\*\/\(\)\.\s]+$', clean_expr): 
        raise ValueError("Caratteri non validi")
    try: 
        return int(eval(clean_expr, {"__builtins__": None}, {}))
    except Exception: 
        raise ValueError("Errore di calcolo")

def format_smart_minecraft(value: int) -> str:
    """Formatta i numeri in Shulker Box e Stack (es. 1SB+5^)."""
    SHULKER, STACK = 1728, 64
    if value < STACK: 
        return str(value)
    
    sb, rem_sb = value // SHULKER, value % SHULKER
    stk, rem_final = rem_sb // STACK, rem_sb % STACK
    parts = []
    
    if sb > 0: parts.append(f"{sb}SB")
    if stk > 0: parts.append(f"{stk}^")
    if rem_final > 0: parts.append(f"{rem_final}")
    
    return f"{value} ({'+'.join(parts)})" if parts else str(value)


# =============================================================================
# 7. MODEL E GESTIONE DATI
# =============================================================================
@dataclass
class Material:
    """Rappresenta un singolo blocco di Minecraft con i relativi conteggi."""
    total: int
    available: int
    
    @property
    def missing(self) -> int: 
        return max(0, self.total - self.available)


class DataManager:
    """Gestisce l'archiviazione e la modifica del database materiali (JSON)."""
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

    def is_ignored(self, category: str) -> bool: 
        return category in self.ignored_categories
        
    def get_ignore_timestamp(self, category: str) -> str: 
        return self.ignored_categories.get(category, "")
        
    def get_all_categories(self) -> List[str]: 
        return sorted(list(self.data.keys()))

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
            match = PATTERN_LITEMATIC_LINE.match(line.strip())
            if match:
                try:
                    name = match.group(1).strip()
                    if name.lower() == 'item': continue 
                    
                    total = int(match.group(2).strip())
                    if name in self.data[category_name]: 
                        self.data[category_name][name].total = total
                    else: 
                        self.data[category_name][name] = Material(total=total, available=0)
                        
                    parsed_count += 1
                    names_found.append(name)
                except (ValueError, IndexError): 
                    continue 
                    
        self._last_imported_names = names_found
        return parsed_count

    def import_from_txt(self, filepath: str, category_name: str) -> int:
        try:
            with open(filepath, 'r', encoding='utf-8') as f: 
                return self._parse_lines(f.readlines(), category_name)
        except Exception: 
            return -1

    def import_from_string(self, text_content: str, category_name: str) -> int:
        return self._parse_lines(text_content.splitlines(), category_name)
 
    def import_from_json(self, filepath: str, category_name: str, recipe_manager: Optional['RecipeManager'] = None) -> int:
        try:
            with open(filepath, 'r', encoding='utf-8') as f: 
                data = json.load(f)
                
            target_category = f"{category_name} // Risorse Grezze" if recipe_manager else category_name
            if target_category not in self.data: 
                self.data[target_category] = {}

            parsed_count = 0
            names_found: List[str] = []
            
            for item in data:
                raw_item, total = item.get("RawItem"), item.get("TotalEstimate")
                if raw_item and total is not None:
                    if recipe_manager:
                        raw_materials = recipe_manager.get_raw_materials(raw_item, int(total))
                        for raw_name, raw_amount in raw_materials.items():
                            formatted_name = raw_name.replace("_", " ").title()
                            if formatted_name in self.data[target_category]: 
                                self.data[target_category][formatted_name].total += raw_amount
                            else: 
                                self.data[target_category][formatted_name] = Material(total=raw_amount, available=0)
                            parsed_count += 1
                            names_found.append(formatted_name)
                    else:
                        name = raw_item.replace("minecraft:", "").replace("_", " ").title()
                        if name in self.data[target_category]: 
                            self.data[target_category][name].total += int(total)
                        else: 
                            self.data[target_category][name] = Material(total=int(total), available=0)
                        parsed_count += 1
                        names_found.append(name)
                        
            self._last_imported_names = names_found
            return parsed_count
        except Exception:
            self._last_imported_names = []
            return -1

    def get_last_imported_names(self) -> List[str]: 
        return list(self._last_imported_names)


# =============================================================================
# 8. RECIPE & TEXTURE MANAGERS
# =============================================================================
class RecipeManager:
    """Calcola i materiali grezzi basati sulle ricette di Minecraft."""
    def __init__(self, recipes_folder: str):
        self.recipes_folder = recipes_folder
        self.recipes = self._load_all_recipes()

    def _load_all_recipes(self) -> dict:
        data = {}
        if not os.path.exists(self.recipes_folder): return data
        for root, _, files in os.walk(self.recipes_folder):
            for f in files:
                if f.endswith(".json"):
                    name = f.replace(".json", "")
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                            data[name] = json.load(file)
                    except json.JSONDecodeError: 
                        pass
        return data

    def get_raw_materials(self, item_name: str, quantity: int = 1) -> dict:
        clean_name = item_name.replace("minecraft:", "")
        if clean_name not in self.recipes: 
            return {clean_name: quantity}
            
        recipe = self.recipes[clean_name]
        raw_materials = {}
        result_count = recipe["result"].get("count", 1) if "result" in recipe and isinstance(recipe["result"], dict) else 1
        crafts_needed = (quantity + result_count - 1) // result_count 
        ingredients = self._parse_ingredients(recipe)
        
        for ing_name, ing_amount in ingredients.items():
            total_ing_amount = ing_amount * crafts_needed
            sub_materials = self.get_raw_materials(ing_name, total_ing_amount)
            for sub_name, sub_amount in sub_materials.items():
                raw_materials[sub_name] = raw_materials.get(sub_name, 0) + sub_amount
        return raw_materials

    def _parse_ingredients(self, recipe: dict) -> dict:
        ingredients_list = {}
        if recipe.get("type") == "minecraft:crafting_shaped":
            keys_count = {}
            for row in recipe.get("pattern", []):
                for char in row:
                    if char != " ": keys_count[char] = keys_count.get(char, 0) + 1
            for key_symbol, count in keys_count.items():
                item_name = self._resolve_ingredient(recipe.get("key", {}).get(key_symbol, {}))
                if item_name: 
                    ingredients_list[item_name] = ingredients_list.get(item_name, 0) + count
        elif recipe.get("type") == "minecraft:crafting_shapeless":
            for ingredient_dict in recipe.get("ingredients", []):
                item_name = self._resolve_ingredient(ingredient_dict)
                if item_name: 
                    ingredients_list[item_name] = ingredients_list.get(item_name, 0) + 1
        return ingredients_list

    def _resolve_ingredient(self, ingredient_dict) -> str:
        if isinstance(ingredient_dict, list) and len(ingredient_dict) > 0: 
            ingredient_dict = ingredient_dict[0]
            
        if "item" in ingredient_dict: 
            return ingredient_dict["item"].replace("minecraft:", "")
        elif "tag" in ingredient_dict: 
            return ingredient_dict["tag"].replace("minecraft:", "").replace("#", "")
        return ""


class TextureManager:
    """Gestisce l'indicizzazione intelligente, la cache e la risoluzione automatica dei modelli delle icone di Minecraft."""
    ICON_SIZE = (20, 20)
    BAD_FOLDERS = ("gui", "font", "colormap", "effect", "particle", "environment", "debug", "placeholder", "misc", "model")
    ALIASES = {
        "tuff_brick_stairs": "tuff_bricks", "tuff_brick_slab": "tuff_bricks", "tuff_brick_wall": "tuff_bricks",
        "redstone_dust": "redstone", "redstone_repeater": "repeater", "redstone_comparator": "comparator",
        "sticky_piston": "piston_top_sticky", "piston": "piston_top_normal", "lever": "lever",
        "tripwire_hook": "tripwire_hook", "observer": "observer_front", "dispenser": "dispenser_front",
        "dropper": "dropper_front", "hopper": "hopper_inside", "lectern": "lectern_top",
        "loom": "loom_front", "smithing_table": "smithing_table_front", "fletching_table": "fletching_table_front",
        "cartography_table": "cartography_table_top", "crafting_table": "crafting_table_front",
        "ender_chest": "ender_eye", "vines": "vine", "lily_pad": "lily_pad", "wheat_seeds": "wheat_seeds",
        "bamboo": "bamboo_stalk", "sugar_cane": "sugar_cane", "glass_pane": "glass",
        "white_stained_glass_pane": "white_stained_glass", "stripped_spruce_wood": "stripped_spruce_log",
        "stripped_oak_wood": "stripped_oak_log", "stripped_birch_wood": "stripped_birch_log",
        "stripped_jungle_wood": "stripped_jungle_log", "stripped_acacia_wood": "stripped_acacia_log",
        "stripped_dark_oak_wood": "stripped_dark_oak_log", "stripped_mangrove_wood": "stripped_mangrove_log",
        "stripped_cherry_wood": "stripped_cherry_log", "stripped_crimson_hyphae": "stripped_crimson_stem",
        "stripped_warped_hyphae": "stripped_warped_stem",
    }

    def __init__(self, script_dir):
        self.script_dir, self.cache, self.index = script_dir, {}, {}
        self.models_path = os.path.join(script_dir, "assets", "minecraft", "models", "item")
        self.cache_file = os.path.join(script_dir, ".texture_index_cache.json")
        self._load_or_build_index()

    def _load_or_build_index(self):
        rebuild_needed = True
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f: 
                    self.index = json.load(f)
                if self.index and os.path.exists(next(iter(self.index.values()))): 
                    rebuild_needed = False
            except Exception: 
                pass
            
        if rebuild_needed:
            self.index = {}
            for folder in [os.path.join(self.script_dir, d) for d in ["2D - Assets 2", "2D - Assets", "assets", "textures"]]:
                if os.path.exists(folder):
                    for root, _, files in os.walk(folder):
                        if any(x in root.lower() for x in self.BAD_FOLDERS): continue
                        for f in files:
                            if f.lower().endswith(".png"):
                                key, full = os.path.splitext(f)[0].lower(), os.path.join(root, f)
                                if key not in self.index or ("2d - assets" not in self.index[key].lower() and ("block" in full or "item" in full)):
                                    self.index[key] = full
            try:
                with open(self.cache_file, "w", encoding="utf-8") as f: 
                    json.dump(self.index, f)
            except Exception: 
                pass

    def _read_json_model(self, item_name):
        if not os.path.exists(self.models_path): return None
        json_path = os.path.join(self.models_path, f"{item_name}.json")
        if not os.path.exists(json_path): return None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                if "textures" in content and "layer0" in content["textures"]: 
                    return content["textures"]["layer0"].split("/")[-1]
        except Exception: 
            pass
        return None

    def get_icon(self, name):
        clean = name.lower().strip().replace(" ", "_")
        if clean in self.cache: 
            return self.cache[clean]
            
        candidates = []
        if clean in self.ALIASES: candidates.append(self.ALIASES[clean])
        json_texture = self._read_json_model(clean)
        
        if json_texture: candidates.append(json_texture)
        candidates.append(clean)
        
        for suffix in ["_stairs", "_slab", "_fence_gate", "_fence", "_button", "_pressure_plate", "_wall", "_door", "_trapdoor", "_sign"]:
            if clean.endswith(suffix):
                base = clean.replace(suffix, "")
                candidates.extend([base, base + "s" if base.endswith("brick") else None, base + "_planks", base + "_block"])
        
        candidates.extend([clean + "_side", clean + "_front", clean + "_top"])
        if "wood" in clean: candidates.append(clean.replace("wood", "log"))
        
        unique = []
        for c in candidates: 
            if c and c not in unique: unique.append(c)

        path = next((self.index[c] for c in unique if c in self.index), None)
        if not path: 
            path = next((fp for fn, fp in self.index.items() if clean in fn and len(fn) < len(clean) + 5), None)

        if not path:
            self.cache[clean] = None
            return None
            
        try:
            img = Image.open(path).resize(self.ICON_SIZE, Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.cache[clean] = tk_img
            return tk_img
        except Exception:
            self.cache[clean] = None
            return None


# =============================================================================
# 9. FINESTRE DI DIALOGO (UI)
# =============================================================================
class CustomDialogBase(tk.Toplevel):
    """Finestra di base con stile applicato automaticamente."""
    def __init__(self, parent, title_text, size="400x350"):
        super().__init__(parent)
        self.title(title_text)
        self.geometry(size)
        self.transient(parent)
        self.grab_set()
        pywinstyles.apply_style(self, "dark") 

class NewMaterialDialog(CustomDialogBase):
    def __init__(self, parent, title_text, main_categories: list, material_data: Optional[dict] = None):
        super().__init__(parent, title_text, "400x420")
        self.result = None
        self.material_data = material_data or {}
        
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Categoria Principale:").pack(anchor="w", pady=(0,5))
        self.main_combo = ttk.Combobox(frame, values=main_categories)
        self.main_combo.pack(fill="x", pady=(0,15))
        self.main_combo.set(self.material_data.get('main_category', 'Progetti'))

        ttk.Label(frame, text="Sottocategoria:").pack(anchor="w", pady=(0,5))
        self.sub_entry = ttk.Entry(frame)
        self.sub_entry.pack(fill="x", pady=(0,15))
        self.sub_entry.insert(0, self.material_data.get('sub_category', 'Generale'))

        ttk.Label(frame, text="Nome Materiale:").pack(anchor="w", pady=(0,5))
        self.nome_entry = ttk.Entry(frame)
        self.nome_entry.pack(fill="x", pady=(0,15))
        self.nome_entry.insert(0, self.material_data.get('name', ''))

        cols = ttk.Frame(frame)
        cols.pack(fill="x", pady=(0, 20))
        
        col1 = ttk.Frame(cols)
        col1.pack(side="left", fill="x", expand=True, padx=(0,5))
        ttk.Label(col1, text="Totale (es. 5sb, 64*5):").pack(anchor="w", pady=(0,5))
        self.totale_entry = ttk.Entry(col1)
        self.totale_entry.pack(fill="x")
        self.totale_entry.insert(0, str(self.material_data.get('total', '')))

        col2 = ttk.Frame(cols)
        col2.pack(side="right", fill="x", expand=True, padx=(5,0))
        ttk.Label(col2, text="Disponibile:").pack(anchor="w", pady=(0,5))
        self.disponibile_entry = ttk.Entry(col2)
        self.disponibile_entry.pack(fill="x")
        self.disponibile_entry.insert(0, str(self.material_data.get('available', '0')))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Salva Materiale", command=self.on_submit, style="Accent.TButton").pack(side="right")
        self.wait_window()

    def on_submit(self):
        main_cat = self.main_combo.get().strip().title()
        sub_cat = self.sub_entry.get().strip().title()
        nome = self.nome_entry.get().strip().title()
        
        if not main_cat or not nome: return
        if not sub_cat: sub_cat = "Generale"
         
        try:
            tot = evaluate_math_expression(self.totale_entry.get() or "0")
            disp = evaluate_math_expression(self.disponibile_entry.get() or "0")
            
            if tot < 0: tot = 0
            if disp < 0: disp = 0
            if disp > tot: disp = tot
        except ValueError:
            modern_messagebox(self, "Errore di Inserimento", "Inserisci numeri validi o espressioni matematiche.", "error")
            return
            
        self.result = {"main_category": main_cat, "sub_category": sub_cat, "name": nome, "total": tot, "available": disp}
        self.destroy()

class PasteImportDialog(CustomDialogBase):
    def __init__(self, parent, main_categories: list):
        super().__init__(parent, "Importa dagli Appunti", "500x500")
        self.result = None
        
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Categoria Principale:").pack(anchor="w")
        self.main_combo = ttk.Combobox(frame, values=main_categories)
        self.main_combo.pack(fill="x", pady=(2, 10))
        self.main_combo.set("Progetti")

        ttk.Label(frame, text="Sottocategoria:").pack(anchor="w")
        self.sub_entry = ttk.Entry(frame)
        self.sub_entry.pack(fill="x", pady=(2, 10))
        self.sub_entry.insert(0, "Importato da Appunti")

        ttk.Label(frame, text="Incolla la tua lista qui (| Nome | Quantità |):").pack(anchor="w")
        self.text_area = tk.Text(frame, wrap="none", font=("Consolas", 10), bg="#1e1e1e", fg="#ffffff", insertbackground="#ffffff", relief="flat")
        self.text_area.pack(fill="both", expand=True, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10,0))
        ttk.Button(btn_frame, text="Importa Dati", command=self.on_import, style="Accent.TButton").pack(side="right")
        self.wait_window()

    def on_import(self):
        main_cat = self.main_combo.get().strip().title()
        sub_cat = self.sub_entry.get().strip().title()
        content = self.text_area.get("1.0", tk.END).strip()
        
        if not main_cat or not content: return
        if not sub_cat: sub_cat = "Generale"
        
        self.result = (f"{main_cat} // {sub_cat}", content)
        self.destroy()

class ProjectSummaryDialog(CustomDialogBase):
    def __init__(self, parent, data: Dict[str, Dict[str, Material]], ignored_cats: dict):
        super().__init__(parent, "Sommario Progetto", "550x600")
        
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="MATERIALI TOTALI RICHIESTI", font=("Segoe UI Variable Display", 12, "bold")).pack(pady=(0,10))
        
        text_area = tk.Text(frame, font=("Consolas", 10), bg="#1e1e1e", fg="#ffffff", relief="flat", padx=10, pady=10)
        text_area.pack(fill="both", expand=True)
        
        totals = {}
        for cat, items in data.items():
            if cat in ignored_cats: continue
            for name, mat in items.items():
                clean_name = name.lower()
                if clean_name not in totals:
                    totals[clean_name] = {"total": 0, "missing": 0}
                totals[clean_name]["total"] += mat.total
                totals[clean_name]["missing"] += mat.missing
                
        sorted_names = sorted(totals.keys())
        lines = [f"{'MATERIALE':<30} | {'MANCANTI / TOTALI':<30}", "-" * 65]
        for name in sorted_names:
            t = totals[name]
            if t["total"] == 0: continue
            lines.append(f"{name.title():<30} | {format_smart_minecraft(t['missing'])} / {format_smart_minecraft(t['total'])}")
            
        text_area.insert("1.0", "\n".join(lines))
        text_area.config(state="disabled")
        
        ttk.Button(frame, text="Chiudi", command=self.destroy).pack(pady=(15,0))


# =============================================================================
# 10. CLASSE PRINCIPALE: MATERIAL GUI
# =============================================================================
class MaterialGUI:
    """Gestisce la finestra principale e coordina Model e View."""
    def __init__(self, root: TkinterDnD.Tk):
        self.root = root
        
        # Inizializza Temi
        sv_ttk.set_theme("dark")
        pywinstyles.apply_style(self.root, "dark")
        
        script_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.texture_manager = TextureManager(script_dir)
        
        # Configurazione
        config = load_config()
        self.save_directory = config.get("save_directory", "")
        self.import_directory = config.get("import_directory", self.save_directory)
        
        if "window_geometry" in config:
            self.root.geometry(config["window_geometry"])
            
        if not self.save_directory or not os.path.isdir(self.save_directory):
            self.save_directory = filedialog.askdirectory(title="Scegli una cartella per i salvataggi")
            if not self.save_directory:
                self.root.destroy()
                return
            save_config({"save_directory": self.save_directory, "import_directory": self.save_directory})
            
        self.data_filepath = os.path.join(self.save_directory, "construction_materials.json")
        self.data_manager = DataManager(self.data_filepath)
        
        self.show_missing_only = tk.BooleanVar(value=False)
        self.hide_completed = tk.BooleanVar(value=False)
        self.always_on_top_var = tk.BooleanVar(value=False)
        
        # Variabili Paginazione Anti-lag
        self.current_page = 0
        self.items_per_page = 15
        
        saved_cols = config.get("column_visibility", {})
        self.column_visibility = {
            "Total": tk.BooleanVar(value=saved_cols.get("Total", True)),
            "Missing": tk.BooleanVar(value=saved_cols.get("Missing", True)),
            "Available": tk.BooleanVar(value=saved_cols.get("Available", True))
        }
        self._ignore_select = False
        
        # Assemblaggio Grafica
        self._configure_treeview_tags()
        self.update_window_title()
        self._create_custom_menubar()
        self._create_widgets()
        self._create_context_menu()
        self._bind_shortcuts()
        
        # Attivazione Drag&Drop
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self._on_file_drop)
        
        self.refresh_treeview()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_treeview_tags(self):
        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=("Segoe UI Variable Text", 10))
        style.configure("Treeview.Heading", font=("Segoe UI Variable Display", 10, "bold"))
        self.root.option_add("*Treeview.Treearea.font", ("Segoe UI Variable Text", 10))

    def _create_custom_menubar(self):
        self.menu_frame = tk.Frame(self.root, bg="#1e1e1e", height=30)
        self.menu_frame.pack(side="top", fill="x")
        
        def create_menu(parent_btn):
            return tk.Menu(parent_btn, tearoff=0, bg="#2b2b2b", fg="white", activebackground=BLURPLE, activeforeground="white", bd=0, font=("Segoe UI", 9))
            
        file_btn = tk.Menubutton(self.menu_frame, text=" File ", bg="#1e1e1e", fg="white", activebackground=BLURPLE, relief="flat", padx=10, font=("Segoe UI", 10))
        file_btn.pack(side="left")
        fm = create_menu(file_btn)
        file_btn.config(menu=fm)
        fm.add_command(label="📁 Apri Cartella Salvataggi", command=lambda: os.startfile(self.save_directory))
        fm.add_command(label="📥 Importa da File (.txt/.json)", command=self.import_file_dialog)
        fm.add_command(label="📋 Importa da Appunti", command=self.import_from_clipboard)
        fm.add_separator()
        fm.add_command(label="📊 Esporta Sommario CSV", command=self.export_csv)
        fm.add_separator()
        fm.add_command(label="⚙️ Impostazioni", command=self.show_settings)
        fm.add_command(label="❌ Esci", command=self._on_close)
        
        view_btn = tk.Menubutton(self.menu_frame, text=" Visualizza ", bg="#1e1e1e", fg="white", activebackground=BLURPLE, relief="flat", padx=10, font=("Segoe UI", 10))
        view_btn.pack(side="left")
        vm = create_menu(view_btn)
        view_btn.config(menu=vm)
        vm.add_checkbutton(label="📌 Sempre in Primo Piano", variable=self.always_on_top_var, command=self.toggle_always_on_top)
        vm.add_separator()
        
        cols_menu = create_menu(vm)
        vm.add_cascade(label="Colonne Visibili", menu=cols_menu)
        for col_name, var in self.column_visibility.items():
            cols_menu.add_checkbutton(label=col_name, variable=var, command=self.refresh_treeview)
            
        help_btn = tk.Menubutton(self.menu_frame, text=" Aiuto ", bg="#1e1e1e", fg="white", activebackground=BLURPLE, relief="flat", padx=10, font=("Segoe UI", 10))
        help_btn.pack(side="left")
        hm = create_menu(help_btn)
        help_btn.config(menu=hm)
        hm.add_command(label="ℹ️ Scorciatoie", command=lambda: modern_messagebox(self.root, "Scorciatoie", "+ / - : Aggiungi/Rimuovi 1\nShift + + : Aggiungi 1 Stack (64)\nShift + - : Rimuovi 1 Stack (64)\nDel : Elimina selezionati\nC : Copia nome materiale", "info"))

    def _on_search_change(self, *args):
        if hasattr(self, 'search_timer') and self.search_timer:
            self.root.after_cancel(self.search_timer)
        self.search_timer = self.root.after(250, self.refresh_treeview)

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill="both", expand=True)
        
        # [Il resto del setup grafico dei widget principali e Notebook progetti va qui...]
        pass

    def _create_context_menu(self):
        pass

    def _bind_shortcuts(self):
        pass

    def _on_file_drop(self, event):
        pass

    def refresh_treeview(self):
        pass

    def update_window_title(self):
        self.root.title("Material Dreamer - Gestore Risorse Minecraft")

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def import_file_dialog(self):
        pass

    def import_from_clipboard(self):
        pass

    def export_csv(self):
        pass

    def show_settings(self):
        pass

    def _on_close(self):
        """Salva i dati e chiude in sicurezza l'applicazione."""
        self.data_manager.save_data()
        
        config = load_config()
        config["save_directory"] = self.save_directory
        config["import_directory"] = self.import_directory
        config["window_geometry"] = self.root.geometry()
        config["column_visibility"] = {k: v.get() for k, v in self.column_visibility.items()}
        
        save_config(config)
        self.root.destroy()


# =============================================================================
# 11. BOOTSTRAP APPLICAZIONE
# =============================================================================
def main():
    root = TkinterDnD.Tk()
    root.withdraw()
    
    app = MaterialGUI(root)
    
    window_width, window_height = 1100, 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    
    config = load_config()
    if "window_geometry" not in config:
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    root.deiconify()
    root.mainloop()

if __name__ == "__main__":
    main()