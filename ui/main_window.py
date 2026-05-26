# ui/main_window.py
import os
import sys
import re
import json
import shutil
from typing import List, Optional, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox, Toplevel
import pywinstyles
import sv_ttk

from core.config import *
from core.utils import *
# Rimosso RecipeManager da qui!
from core.database import DataManager, Material
from ui.textures import TextureManager
from ui.components import (
    modern_messagebox, modern_askyesno, CustomDialogBase,
    NewMaterialDialog, PasteImportDialog, ProjectSummaryDialog, ModernProgressBar
)

class MaterialGUI:
    def __init__(self, root):
        self.root = root
        self.script_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        if "ui" in self.script_dir.lower():
            self.script_dir = os.path.dirname(self.script_dir) # Risale se si trova in ui/
            
        config = load_config()
        self.save_directory = config.get("save_directory", "")
        self.import_directory = config.get("import_directory", self.save_directory)
        
        if not self.save_directory or not os.path.isdir(self.save_directory):
            self.save_directory = filedialog.askdirectory(title="Scegli una cartella per i salvataggi")
            if not self.save_directory:
                self.root.destroy()
                return
            save_config({"save_directory": self.save_directory, "import_directory": self.save_directory})
            
        self.data_filepath = os.path.join(self.save_directory, "construction_materials.json")
        self.data_manager = DataManager(self.data_filepath)
        self.texture_manager = TextureManager(self.script_dir)
        
        self.items_per_page = 40
        self.current_page = 0
        self._ignore_select = False
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search_change())
        self.hide_completed = tk.BooleanVar(value=False)
        self.show_missing_only = tk.BooleanVar(value=False)
        self.always_on_top_var = tk.BooleanVar(value=False)
        
        self.column_visibility = {
            "Richiesto": tk.BooleanVar(value=config.get("column_visibility", {}).get("Richiesto", True)),
            "Mancante": tk.BooleanVar(value=config.get("column_visibility", {}).get("Mancante", True)),
            "Disponibile": tk.BooleanVar(value=config.get("column_visibility", {}).get("Disponibile", True))
        }
        
        self._setup_theme()
        self._build_main_layout()
        self._create_context_menu()
        self._bind_shortcuts()
        
        self.update_window_title()
        self.refresh_treeview()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_theme(self):
        sv_ttk.set_theme("dark")
        pywinstyles.apply_style(self.root, "dark")
        
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI Variable Text", 10), rowheight=28, background="#1e1e1e", fieldbackground="#1e1e1e")
        style.configure("Treeview.Heading", font=("Segoe UI Variable Display", 10, "bold"), padding=5)
        style.configure("TPanedwindow", background="#1e1e1e")

    def _build_main_layout(self):
        top_bar = ttk.Frame(self.root, padding=5)
        top_bar.pack(fill="x", side="top")
        
        ttk.Button(top_bar, text="💾 Salva", command=self.data_manager.save_data, width=10).pack(side="left", padx=2)
        ttk.Button(top_bar, text="📥 Importa File", command=self.import_file_dialog, width=15).pack(side="left", padx=2)
        ttk.Button(top_bar, text="📋 Incolla Testo", command=self.import_from_clipboard, width=15).pack(side="left", padx=2)
        ttk.Button(top_bar, text="📊 Riepilogo", command=self.show_project_summary, width=12).pack(side="left", padx=2)
        ttk.Button(top_bar, text="➕ Aggiungi", command=self.add_material_dialog, style="Accent.TButton", width=12).pack(side="left", padx=2)
        
        ttk.Checkbutton(top_bar, text="Sempre in Primo Piano", variable=self.always_on_top_var, command=self.toggle_always_on_top).pack(side="right", padx=5)
        ttk.Button(top_bar, text="⚙️ Impostazioni", command=self.show_settings, width=14).pack(side="right", padx=2)
        
        filter_bar = ttk.Frame(self.root, padding=5)
        filter_bar.pack(fill="x")
        
        ttk.Label(filter_bar, text="🔍 Cerca: ").pack(side="left", padx=2)
        self.search_entry = ttk.Entry(filter_bar, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left", padx=5)
        
        ttk.Checkbutton(filter_bar, text="Nascondi completati", variable=self.hide_completed, command=self.refresh_treeview).pack(side="left", padx=10)
        ttk.Checkbutton(filter_bar, text="Solo risorse mancanti", variable=self.show_missing_only, command=self.refresh_treeview).pack(side="left", padx=10)
        
        ttk.Button(filter_bar, text="📂 Espandi tutto", command=lambda: self.toggle_all_folders(True)).pack(side="right", padx=2)
        ttk.Button(filter_bar, text="📁 Riduci tutto", command=lambda: self.toggle_all_folders(False)).pack(side="right", padx=2)
        
        self.pane = ttk.Panedwindow(self.root, orient="horizontal")
        self.pane.pack(fill="both", expand=True, padx=5, pady=5)
        
        tree_frame = ttk.Frame(self.pane)
        self.pane.add(tree_frame, weight=4)
        
        self.tree = ttk.Treeview(tree_frame, columns=("Richiesto", "Mancante", "Disponibile"), show="tree headings")
        self.tree.heading("#0", text="Struttura Categorie / Materiale", anchor="w")
        self.tree.heading("Richiesto", text="Totale Richiesto")
        self.tree.heading("Mancante", text="Mancante")
        self.tree.heading("Disponibile", text="Disponibile")
        
        self.tree.column("#0", width=450, anchor="w")
        self.tree.column("Richiesto", width=160, anchor="center")
        self.tree.column("Mancante", width=160, anchor="center")
        self.tree.column("Disponibile", width=160, anchor="center")
        
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        self.slider_panel = ttk.LabelFrame(self.pane, text=" Regolazione Rapida Qtà ", padding=10)
        self.pane.add(self.slider_panel, weight=1)
        self.slider_panel.pack_forget()
        
        self.slider_title_lbl = ttk.Label(self.slider_panel, text="Blocco Selezionato", font=("Segoe UI", 10, "bold"), wraplength=180)
        self.slider_title_lbl.pack(fill="x", pady=(0, 10))
        
        self.quick_scale = ttk.Scale(self.slider_panel, from_=0, to=100, orient="horizontal", command=self._on_slider_scroll)
        self.quick_scale.pack(fill="x", pady=5)
        
        self.slider_val_lbl = ttk.Label(self.slider_panel, text="0 / 0", font=("Consolas", 11, "bold"), anchor="center")
        self.slider_val_lbl.pack(fill="x", pady=5)
        
        if hasattr(self.root, 'drop_target_register'):
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self._on_file_drop)
            
        self.bottom_bar = ttk.Frame(self.root, padding=2)
        self.bottom_bar.pack(fill="x", side="bottom")
        
        self.progress_bar = ModernProgressBar(self.bottom_bar)
        self.progress_bar.pack(fill="x", pady=2)
        
        self.pagination_frame = ttk.Frame(self.bottom_bar)
        self.pagination_frame.pack(fill="x", pady=2)
        
        self.btn_prev_page = ttk.Button(self.pagination_frame, text="◀ Precedente", command=self._prev_page, width=15)
        self.btn_prev_page.pack(side="left", padx=10)
        self.btn_next_page = ttk.Button(self.pagination_frame, text="Successiva ▶", command=self._next_page, width=15)
        self.btn_next_page.pack(side="right", padx=10)
        
        self.page_label = ttk.Label(self.pagination_frame, text="Pagina 1/1", anchor="center")
        self.page_label.pack(fill="x", expand=True, pady=4)

    def _on_search_change(self):
        self.current_page = 0
        self.refresh_treeview()

    def _hide_slider(self):
        if self.slider_panel.winfo_ismapped():
            self.slider_panel.pack_forget()

    def _on_tree_select(self, event):
        if self._ignore_select: return
        sel = self.tree.selection()
        if not sel:
            self._hide_slider()
            return
            
        item_id = sel[0]
        tags = self.tree.item(item_id, "tags")
        
        if any(t in tags for t in ('completed', 'partial', 'unstarted')):
            nome = self.tree.item(item_id, "text").strip().replace(" ✓", "")
            for cat_items in self.data_manager.data.values():
                if nome in cat_items:
                    mat = cat_items[nome]
                    self.slider_title_lbl.configure(text=nome)
                    self.quick_scale.configure(to=max(1, mat.total))
                    self._ignore_select = True
                    self.quick_scale.set(mat.available)
                    self._ignore_select = False
                    self.slider_val_lbl.configure(text=f"{mat.available} / {mat.total}")
                    if not self.slider_panel.winfo_ismapped():
                        self.slider_panel.pack(side="right", fill="both", before=self.tree.master)
                    return
        self._hide_slider()

    def _on_slider_scroll(self, value):
        if self._ignore_select: return
        sel = self.tree.selection()
        if not sel: return
        
        item_id = sel[0]
        new_val = int(float(value))
        nome = self.tree.item(item_id, "text").strip().replace(" ✓", "")
        
        for cat_items in self.data_manager.data.values():
            if nome in cat_items:
                mat = cat_items[nome]
                new_val = max(0, min(mat.total, new_val))
                self.slider_val_lbl.configure(text=f"{new_val} / {mat.total}")
                self._update_material_amount(item_id, new_val)
                break

    def _create_context_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="white", bd=0)
        self.menu.add_command(label="📝 Modifica Materiale", command=self.edit_material)
        self.menu.add_command(label="🗑️ Elimina", command=self.delete_selected)
        self.menu.add_separator()
        self.menu.add_command(label="📋 Copia Nome", command=self.copy_material_name)
        
        self.cat_menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="white", bd=0)
        self.cat_menu.add_command(label="✏️ Rinomina Sottocategoria", command=self.rename_category)
        self.cat_menu.add_command(label="👁️ Ignora/Riattiva", command=self.toggle_ignore)
        self.cat_menu.add_separator()
        self.cat_menu.add_command(label="🗑️ Elimina Sottocategoria", command=self.delete_category)

        self.main_menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="white", bd=0)
        self.main_menu.add_command(label="➕ Aggiungi Sottocartella / Materiale", command=self.add_material_to_main)
        self.main_menu.add_command(label="📥 Importa File in questo Gruppo", command=self.import_file_to_main)
        self.main_menu.add_separator()
        self.main_menu.add_command(label="✏️ Rinomina Intero Gruppo", command=self.rename_category)
        self.main_menu.add_command(label="🗑️ Elimina Intero Gruppo", command=self.delete_category)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return
        self.tree.selection_set(item)
        
        if str(item).startswith("MAIN__"):
            self.main_menu.post(event.x_root, event.y_root)
        elif str(item).startswith("CAT__"):
            self.cat_menu.post(event.x_root, event.y_root)
        else:
            self.menu.post(event.x_root, event.y_root)

    def refresh_treeview(self):
        self._hide_slider()
        
        search = self.search_var.get().lower()
        hide_comp = self.hide_completed.get()
        missing_only = self.show_missing_only.get()
        is_searching = len(search) > 0
        
        self.tree.delete(*self.tree.get_children())
        
        visible_cols = [c for c, v in self.column_visibility.items() if v.get()]
        self.tree["displaycolumns"] = visible_cols

        all_filtered_mats = []
        for cat_key, items in self.data_manager.data.items():
            is_cat_ignored = self.data_manager.is_ignored(cat_key)
            if is_searching and is_cat_ignored: 
                continue
                
            main_cat, sub_cat = cat_key.split(" // ", 1) if " // " in cat_key else (cat_key, "Generale")
            
            for name, mat in items.items():
                if is_searching and (search not in name.lower() and search not in sub_cat.lower() and search not in main_cat.lower()): 
                    continue
                if (hide_comp or missing_only) and mat.missing == 0: 
                    continue
                all_filtered_mats.append((main_cat, sub_cat, cat_key, name, mat, is_cat_ignored))

        all_filtered_mats.sort(key=lambda x: (x[0], x[1], x[3]))
        total_items = len(all_filtered_mats)

        if is_searching:
            items_to_show = all_filtered_mats
            self.pagination_frame.pack_forget() 
        else:
            self.pagination_frame.pack(side="bottom", fill="x")
            max_pages = max(0, (total_items - 1) // self.items_per_page) if total_items > 0 else 0
            if self.current_page > max_pages: 
                self.current_page = max_pages
            
            start_idx = self.current_page * self.items_per_page
            end_idx = start_idx + self.items_per_page
            items_to_show = all_filtered_mats[start_idx:end_idx]
            
            if total_items == 0:
                self.page_label.config(text="Nessun elemento trovato")
            else:
                self.page_label.config(text=f"Elementi {start_idx+1}-{min(end_idx, total_items)} di {total_items}  (Pagina {self.current_page+1}/{max_pages+1})")
                
            self.btn_prev_page.config(state="normal" if self.current_page > 0 else "disabled")
            self.btn_next_page.config(state="normal" if end_idx < total_items else "disabled")

        inserted_main_nodes = {}
        inserted_sub_nodes = {}

        for main_cat, sub_cat, cat_key, name, mat, is_cat_ignored in items_to_show:
            main_iid = f"MAIN__{main_cat}"
            cat_iid = f"CAT__{cat_key}"
            
            if main_iid not in inserted_main_nodes:
                self.tree.insert("", "end", iid=main_iid, text=main_cat, tags=('main_category',), open=True)
                inserted_main_nodes[main_iid] = True
                
            if cat_iid not in inserted_sub_nodes:
                cat_text = f"{sub_cat} (Ignorato)" if is_cat_ignored else sub_cat
                self.tree.insert(main_iid, "end", iid=cat_iid, text=cat_text, tags=('category_ignored' if is_cat_ignored else 'category',), open=True)
                inserted_sub_nodes[cat_iid] = True
            
            self._insert_material_row(cat_iid, name, mat, is_cat_ignored)

        self.tree.tag_configure('main_category', font=("Segoe UI Variable Display", 11, "bold"), background="#2b2d31")
        self.tree.tag_configure('category', font=("Segoe UI Variable Text", 10, "bold"), background="#383a40")
        self.tree.tag_configure('category_ignored', font=("Segoe UI Variable Text", 10, "italic"), foreground=TEXT_MUTED)
        self.tree.tag_configure('completed', foreground=GREEN)
        self.tree.tag_configure('partial', foreground=YELLOW)
        self.tree.tag_configure('unstarted', foreground=TEXT_MAIN)
        self.tree.tag_configure('ignored_item', foreground=TEXT_MUTED)
        
        self.update_global_progress()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_treeview()

    def _next_page(self):
        self.current_page += 1
        self.refresh_treeview()

    def _insert_material_row(self, parent_iid, name, mat, is_cat_ignored):
        is_completed = mat.total > 0 and mat.available >= mat.total
        status_tag = 'ignored_item' if is_cat_ignored else ('completed' if is_completed else 'partial' if mat.available > 0 else 'unstarted')
        checkmark = " ✓" if (is_completed and not is_cat_ignored) else ""
        
        insert_params = {
            "text": f" {name}{checkmark}",
            "values": (format_smart_minecraft(mat.total), format_smart_minecraft(mat.missing), format_smart_minecraft(mat.available)),
            "tags": (status_tag,)
        }
        icon_image = self.texture_manager.get_icon(name)
        if icon_image: 
            insert_params["image"] = icon_image
            
        self.tree.insert(parent_iid, "end", **insert_params)

    def _bind_shortcuts(self):
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.root.bind("<plus>", lambda e: self._quick_math(1))
        self.root.bind("<KP_Add>", lambda e: self._quick_math(1))
        self.root.bind("<minus>", lambda e: self._quick_math(-1))
        self.root.bind("<KP_Subtract>", lambda e: self._quick_math(-1))
        self.root.bind("<Shift-plus>", lambda e: self._quick_math(64))
        self.root.bind("<Shift-KP_Add>", lambda e: self._quick_math(64))
        self.root.bind("<Shift-minus>", lambda e: self._quick_math(-64))
        self.root.bind("<Shift-KP_Subtract>", lambda e: self._quick_math(-64))
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set() if hasattr(self, 'search_entry') else None)
        self.root.bind("c", lambda e: self.copy_material_name())

    def _quick_math(self, delta):
        selected = self.tree.selection()
        if not selected: return
        
        for item_id in selected:
            tags = self.tree.item(item_id, "tags")
            if any(t in tags for t in ('completed', 'partial', 'unstarted')):
                nome = self.tree.item(item_id, "text").strip().replace(" ✓", "")
                
                for cat_items in self.data_manager.data.values():
                    if nome in cat_items:
                        mat = cat_items[nome]
                        new_val = max(0, min(mat.total, mat.available + delta))
                        self._update_material_amount(item_id, new_val)
                        
                        if item_id == selected[0] and self.slider_panel.winfo_ismapped():
                            self.quick_scale.set(new_val)
                            self.slider_val_lbl.configure(text=f"{new_val} / {mat.total}")
                        break
        
        self._ignore_select = True
        self.tree.selection_set(selected)
        self.tree.focus(selected[0])
        self._ignore_select = False
        return "break"

    def _update_material_amount(self, item_id, new_val):
        nome = self.tree.item(item_id, "text").strip().replace(" ✓", "")
        for cat_key, items in self.data_manager.data.items():
            if nome in items:
                mat = items[nome]
                mat.available = new_val
                
                is_completed = mat.available >= mat.total
                checkmark = " ✓" if is_completed else ""
                status_tag = 'completed' if is_completed else 'partial' if mat.available > 0 else 'unstarted'
                
                self.tree.item(item_id, text=f" {nome}{checkmark}", 
                               values=(format_smart_minecraft(mat.total), 
                                       format_smart_minecraft(mat.missing), 
                                       format_smart_minecraft(mat.available)),
                               tags=(status_tag,))
                break
        self.update_global_progress()

    def update_global_progress(self):
        total_g, avail_g = 0, 0
        for cat_key, items in self.data_manager.data.items():
            if not self.data_manager.is_ignored(cat_key):
                for m in items.values():
                    total_g += m.total
                    avail_g += m.available
        
        perc = (avail_g / total_g * 100) if total_g > 0 else 0
        self.progress_bar.update_bar(avail_g, total_g, f"PROGRESSO TOTALE: {perc:.1f}% ({avail_g} / {total_g})")

    def add_material_dialog(self):
        cats = sorted(list(set(k.split(" // ")[0] for k in self.data_manager.data.keys())))
        d = NewMaterialDialog(self.root, "Nuovo Materiale", cats)
        if d.result:
            cat_key = f"{d.result['main_category']} // {d.result['sub_category']}"
            if cat_key not in self.data_manager.data: self.data_manager.data[cat_key] = {}
            self.data_manager.data[cat_key][d.result['name']] = Material(total=d.result['total'], available=d.result['available'])
            self.refresh_treeview()

    def add_material_to_main(self):
        sel = self.tree.focus()
        if not sel or not str(sel).startswith("MAIN__"): return
        main_cat = str(sel).split("MAIN__", 1)[1]
        
        cats = sorted(list(set(k.split(" // ")[0] for k in self.data_manager.data.keys())))
        d = NewMaterialDialog(self.root, f"Nuova Sottocartella in: {main_cat}", cats, {"main_category": main_cat})
        
        if d.result:
            cat_key = f"{d.result['main_category']} // {d.result['sub_category']}"
            if cat_key not in self.data_manager.data: self.data_manager.data[cat_key] = {}
            self.data_manager.data[cat_key][d.result['name']] = Material(total=d.result['total'], available=d.result['available'])
            self.refresh_treeview()

    def edit_material(self):
        sel = self.tree.focus()
        if not sel or any(str(sel).startswith(p) for p in ("MAIN__", "CAT__", "I0")): return
        
        nome = self.tree.item(sel, "text").strip().replace(" ✓", "")
        for cat_key, items in self.data_manager.data.items():
            if nome in items:
                mat = items[nome]
                main_c, sub_c = cat_key.split(" // ", 1) if " // " in cat_key else (cat_key, "Generale")
                cats = sorted(list(set(k.split(" // ")[0] for k in self.data_manager.data.keys())))
                
                d = NewMaterialDialog(self.root, "Modifica Materiale", cats, 
                                     {"main_category": main_c, "sub_category": sub_c, "name": nome, "total": mat.total, "available": mat.available})
                if d.result:
                    del items[nome]
                    new_cat = f"{d.result['main_category']} // {d.result['sub_category']}"
                    if new_cat not in self.data_manager.data: self.data_manager.data[new_cat] = {}
                    self.data_manager.data[new_cat][d.result['name']] = Material(total=d.result['total'], available=d.result['available'])
                    self.refresh_treeview()
                break

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        if modern_askyesno(self.root, "Elimina", f"Sei sicuro di voler eliminare {len(selected)} elementi?"):
            for sel in selected:
                if str(sel).startswith("CAT__"):
                    cat_key = str(sel).split("CAT__", 1)[1]
                    if cat_key in self.data_manager.data: del self.data_manager.data[cat_key]
                elif str(sel).startswith("MAIN__"):
                    main_cat = str(sel).split("MAIN__", 1)[1]
                    keys_to_del = [k for k in self.data_manager.data.keys() if k.startswith(f"{main_cat} // ") or k == main_cat]
                    for k in keys_to_del: del self.data_manager.data[k]
                else:
                    nome = self.tree.item(sel, "text").strip().replace(" ✓", "")
                    for items in self.data_manager.data.values():
                        if nome in items:
                            del items[nome]
                            break
            self.refresh_treeview()

    def toggle_ignore(self):
        sel = self.tree.focus()
        if not sel or not str(sel).startswith("CAT__"): return
        cat_key = str(sel).split("CAT__", 1)[1]
        self.data_manager.toggle_ignore_category(cat_key)
        self.refresh_treeview()

    def toggle_all_folders(self, force_state=None):
        all_items = self.tree.get_children()
        if not all_items: return
        state = force_state if force_state is not None else not any(self.tree.item(i, "open") for i in all_items)
        for i in all_items:
            self.tree.item(i, open=state)
            for child in self.tree.get_children(i):
                self.tree.item(child, open=state)

    def show_project_summary(self):
        ProjectSummaryDialog(self.root, self.data_manager.data, self.data_manager.ignored_categories)

    def import_file_dialog(self):
        # 🚀 MODIFICATO: Rimossa ogni traccia e calcolo di RecipeManager!
        filepaths = filedialog.askopenfilenames(initialdir=self.import_directory, title="Seleziona file (.json / .txt)", filetypes=[("Material Files", "*.json;*.txt")])
        if not filepaths: return

        self.import_directory = os.path.dirname(filepaths[0])

        for filepath in filepaths:
            filename = os.path.basename(filepath)
            # Rimuoviamo l'estensione per creare il nome del progetto
            proj_name = os.path.splitext(filename)[0]
            
            # Richiamiamo import_from_json o import_from_txt in base al file selezionato
            if filepath.endswith(".json"):
                count = self.data_manager.import_from_json(filepath, proj_name)
            else:
                count = self.data_manager.import_from_txt(filepath, proj_name)
            
            if count > 0:
                modern_messagebox(self.root, "Successo", f"Importato: {filename}\nMateriali analizzati: {count}", "success")
            else:
                modern_messagebox(self.root, "Errore", f"Impossibile leggere o trovare materiali validi in: {filename}", "error")

        self.data_manager.save_data()
        self.current_page = 0
        self.refresh_treeview()

    def import_file_to_main(self):
        # 🚀 MODIFICATO: Rimosso blocco di estrazione Ricette
        sel = self.tree.focus()
        if not sel or not str(sel).startswith("MAIN__"): return
        main_cat = str(sel).split("MAIN__", 1)[1]
        
        path = filedialog.askopenfilename(initialdir=self.import_directory, filetypes=[("Material Files", "*.txt;*.json")])
        if path:
            suggested_sub = os.path.splitext(os.path.basename(path))[0].title()
            sub_cat = simpledialog.askstring("Importa in " + main_cat, f"Nome della nuova Sottocartella per '{os.path.basename(path)}':", initialvalue=suggested_sub)
            
            if sub_cat:
                full_cat = f"{main_cat} // {sub_cat.strip()}"
                count = self.data_manager.import_from_json(path, full_cat) if path.endswith(".json") else self.data_manager.import_from_txt(path, full_cat)
                
                if count > 0:
                    modern_messagebox(self.root, "Importazione", f"Importati {count} materiali nella categoria '{full_cat}'.", "success")
                    self.current_page = 0
                    self.refresh_treeview()
                else: 
                    modern_messagebox(self.root, "Errore", "Nessun materiale valido trovato nel file.", "error")

    def import_from_clipboard(self):
        cats = sorted(list(set(k.split(" // ")[0] for k in self.data_manager.data.keys())))
        d = PasteImportDialog(self.root, cats)
        if d.result:
            count = self.data_manager.import_from_string(d.result[1], d.result[0])
            if count > 0:
                modern_messagebox(self.root, "Successo", f"Importati {count} materiali.", "success")
                self.refresh_treeview()

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV file", "*.csv")])
        if filepath and self.data_manager.export_to_csv(filepath):
            modern_messagebox(self.root, "Successo", "Esportato con successo in CSV.", "success")

    def copy_material_name(self):
        sel = self.tree.selection()
        if not sel: return
        names = [self.tree.item(s, "text").strip().replace(" ✓", "") for s in sel if not self.tree.item(s, "text").strip().startswith(("MAIN__", "CAT__"))]
        if names:
            self.root.clipboard_clear()
            self.root.clipboard_append(", ".join(names))

    def rename_category(self):
        sel = self.tree.focus()
        if not sel: return
        if str(sel).startswith("MAIN__"):
            old_main = str(sel).split("MAIN__", 1)[1]
            new_main = simpledialog.askstring("Rinomina", "Nuovo nome Categoria Principale:", initialvalue=old_main)
            if new_main and new_main != old_main:
                new_main = new_main.strip().title()
                for k in [k for k in self.data_manager.data.keys() if k == old_main or k.startswith(f"{old_main} // ")]:
                    new_key = f"{new_main} // {k.split(' // ', 1)[1]}" if " // " in k else f"{new_main} // Generale"
                    self.data_manager.data[new_key] = self.data_manager.data.pop(k)
                self.refresh_treeview()
        elif str(sel).startswith("CAT__"):
            old_cat = str(sel).split("CAT__", 1)[1]
            old_sub = old_cat.split(" // ", 1)[1] if " // " in old_cat else old_cat
            new_sub = simpledialog.askstring("Rinomina", "Nuovo nome Sottocategoria:", initialvalue=old_sub)
            if new_sub and new_sub != old_sub:
                new_sub = new_sub.strip().title()
                new_cat = f"{old_cat.split(' // ', 1)[0]} // {new_sub}" if " // " in old_cat else new_sub
                self.data_manager.data[new_cat] = self.data_manager.data.pop(old_cat)
                self.refresh_treeview()

    def delete_category(self):
        sel = self.tree.focus()
        if not sel: return
        if str(sel).startswith("CAT__"):
            cat_key = str(sel).split("CAT__", 1)[1]
            if modern_askyesno(self.root, "Elimina Categoria", f"Eliminare definitivamente '{cat_key}'?"):
                del self.data_manager.data[cat_key]
                self.refresh_treeview()
        elif str(sel).startswith("MAIN__"):
            main_cat = str(sel).split("MAIN__", 1)[1]
            if modern_askyesno(self.root, "Elimina Gruppo", f"Eliminare tutte le sottocategorie di '{main_cat}'?"):
                keys = [k for k in self.data_manager.data.keys() if k.startswith(f"{main_cat} // ") or k == main_cat]
                for k in keys: del self.data_manager.data[k]
                self.refresh_treeview()

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def update_window_title(self):
        self.root.title(f"Material Dreamer - {os.path.basename(self.save_directory) if self.save_directory else 'Nuovo Progetto'}")

    def mostra_anteprima_importazione(self, nome_file, conteggio_blocchi):
        d = Toplevel(self.root)
        d.title(f"Anteprima: {nome_file}")
        d.geometry("600x550")
        pywinstyles.apply_style(d, "dark")
        d.transient(self.root)
        d.grab_set()
        
        frame = ttk.Frame(d, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="✨ Anteprima Materiali Trovati", font=("Segoe UI", 14, "bold"), foreground="#f0b232").pack(pady=(0, 5))
        
        tabella = ttk.Treeview(frame, columns=("Blocco", "Quantità"), show="headings", height=10)
        tabella.heading("Blocco", text="Nome Materiale")
        tabella.heading("Quantità", text="Quantità Totale")
        tabella.column("Blocco", width=300, anchor="w")
        tabella.column("Quantità", width=150, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tabella.yview)
        tabella.configure(yscrollcommand=scrollbar.set)
        
        tabella_frame = ttk.Frame(frame)
        tabella_frame.pack(fill="both", expand=True, pady=5)
        tabella.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        totale_blocchi = 0
        for blocco, quantita in sorted(conteggio_blocchi.items(), key=lambda x: x[1], reverse=True):
            tabella.insert("", "end", values=(blocco.title(), format_smart_minecraft(quantita)))
            totale_blocchi += quantita
            
        ttk.Label(frame, text=f"Totale complessivo: {totale_blocchi}", font=("Segoe UI", 10, "bold")).pack(anchor="e", pady=5)
        ttk.Label(frame, text="Scegli o scrivi la Categoria:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 5))
        
        cb_categoria = ttk.Combobox(frame, values=self.data_manager.get_all_categories(), font=("Segoe UI", 11))
        cb_categoria.set(nome_file)
        cb_categoria.pack(fill="x", pady=(0, 15))
        
        def conferma():
            categoria = cb_categoria.get().strip()
            if not categoria: return
            
            cat_data = self.data_manager.data.setdefault(categoria, {})
            
            for nome_blocco, quantita in conteggio_blocchi.items():
                nome_formattato = nome_blocco.replace("_", " ").title()
                if nome_formattato in cat_data:
                    cat_data[nome_formattato].total += quantita
                else:
                    cat_data[nome_formattato] = Material(total=quantita, available=0)
            
            self.data_manager.save_data()
            d.destroy()
            
            self.refresh_treeview()
                
        ttk.Button(frame, text="✅ Conferma Importazione", command=conferma, style="Accent.TButton").pack(fill="x", pady=5)

    def _on_file_drop(self, event):
        percorso = event.data.strip('{}')
        estensione = percorso.lower().split('.')[-1]
        
        if estensione in ['txt', 'json']:
            nome_file = os.path.splitext(os.path.basename(percorso))[0]
            
            # Sfruttiamo i parser robusti appena creati
            # Creiamo una finta categoria "temp" per leggere i dati e contarli
            temp_cat = "__temp_preview__"
            
            if estensione == 'json':
                count = self.data_manager.import_from_json(percorso, temp_cat)
            else:
                count = self.data_manager.import_from_txt(percorso, temp_cat)
                
            if count <= 0 or temp_cat not in self.data_manager.data:
                messagebox.showwarning("File Vuoto", "Non ho trovato materiali validi in questo file.")
                if temp_cat in self.data_manager.data:
                    del self.data_manager.data[temp_cat]
                return
                
            # Raccogliamo i blocchi per l'anteprima
            conteggio = {nome: mat.total for nome, mat in self.data_manager.data[temp_cat].items()}
            
            # Puliamo i dati temporanei!
            del self.data_manager.data[temp_cat]
            
            self.mostra_anteprima_importazione(nome_file, conteggio)
            return

        if estensione == 'litematic':
            messagebox.showwarning("Attenzione", "Ricorda che Litematica bugga i file diretti! Usa l'esportazione in .TXT o .JSON.")
            return

    def show_settings(self):
        d = CustomDialogBase(self.root, "Impostazioni", "500x300")
        frame = ttk.Frame(d, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Cartella Salvataggi:").pack(anchor="w")
        sv = ttk.Entry(frame)
        sv.pack(fill="x", pady=(0,15))
        sv.insert(0, self.save_directory)
        
        ttk.Label(frame, text="Cartella Importazione Predefinita:").pack(anchor="w")
        iv = ttk.Entry(frame)
        iv.pack(fill="x", pady=(0,15))
        iv.insert(0, self.import_directory)
        
        def apply():
            self.save_directory, self.import_directory = sv.get(), iv.get()
            self.data_filepath = os.path.join(self.save_directory, "construction_materials.json")
            self.data_manager.set_filepath(self.data_filepath)
            save_config({"save_directory": self.save_directory, "import_directory": self.import_directory})
            self.update_window_title()
            self.refresh_treeview()
            d.destroy()
            
        ttk.Button(frame, text="Salva Impostazioni", command=apply, style="Accent.TButton").pack(side="right")

    def crea_nuova_scheda_progetto(self, nome_progetto, dati_blocchi):
        if not hasattr(self, 'finestra_progetti') or not self.finestra_progetti.winfo_exists():
            self.finestra_progetti = Toplevel(self.root)
            self.finestra_progetti.title("Progetti Litematic")
            self.finestra_progetti.geometry("700x500")
            pywinstyles.apply_style(self.finestra_progetti, "dark")
            self.notebook_progetti = ttk.Notebook(self.finestra_progetti)
            self.notebook_progetti.pack(fill="both", expand=True, padx=10, pady=10)
            
        frame_scheda = ttk.Frame(self.notebook_progetti)
        self.notebook_
# ui/main_window.py
import os, sys, re, json, shutil
from typing import List, Optional, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox, Toplevel
import pywinstyles, sv_ttk

from core.config import *
from core.utils import *
from core.database import DataManager, Material
from ui.textures import TextureManager
from ui.components import (
    modern_messagebox, modern_askyesno, CustomDialogBase,
    NewMaterialDialog, PasteImportDialog, ProjectSummaryDialog, ModernProgressBar
)

class MaterialGUI:
    def __init__(self, root):
        self.root = root
        self.script_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        if "ui" in self.script_dir.lower(): self.script_dir = os.path.dirname(self.script_dir)
        config = load_config()
        self.save_directory = config.get("save_directory", "")
        self.import_directory = config.get("import_directory", self.save_directory)
        if not self.save_directory or not os.path.isdir(self.save_directory):
            self.save_directory = filedialog.askdirectory(title="Scegli una cartella per i salvataggi")
            if not self.save_directory:
                self.root.destroy()
                return
            save_config({"save_directory": self.save_directory, "import_directory": self.save_directory})
        self.data_filepath = os.path.join(self.save_directory, "construction_materials.json")
        self.data_manager = DataManager(self.data_filepath)
        self.texture_manager = TextureManager(self.script_dir)
        self.items_per_page = 40
        self.current_page = 0
        self._ignore_select = False
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search_change())
        self.hide_completed = tk.BooleanVar(value=False)
        self.show_missing_only = tk.BooleanVar(value=False)
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.column_visibility = {
            "Richiesto": tk.BooleanVar(value=config.get("column_visibility", {}).get("Richiesto", True)),
            "Mancante": tk.BooleanVar(value=config.get("column_visibility", {}).get("Mancante", True)),
            "Disponibile": tk.BooleanVar(value=config.get("column_visibility", {}).get("Disponibile", True))
        }
        self._setup_theme()
        self._build_main_layout()
        self._create_context_menu()
        self._bind_shortcuts()
        self.update_window_title()
        self.refresh_treeview()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_theme(self):
        sv_ttk.set_theme("dark")
        pywinstyles.apply_style(self.root, "dark")
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI Variable Text", 10), rowheight=28, background="#1e1e1e", fieldbackground="#1e1e1e")
        style.configure("Treeview.Heading", font=("Segoe UI Variable Display", 10, "bold"), padding=5)
        style.configure("TPanedwindow", background="#1e1e1e")

    def _build_main_layout(self):
        top_bar = ttk.Frame(self.root, padding=5)
        top_bar.pack(fill="x", side="top")
        ttk.Button(top_bar, text="💾 Salva", command=self.data_manager.save_data, width=10).pack(side="left", padx=2)
        ttk.Button(top_bar, text="📥 Importa File", command=self.import_file_dialog, width=15).pack(side="left", padx=2)
        ttk.Button(top_bar, text="📋 Incolla Testo", command=self.import_from_clipboard, width=15).pack(side="left", padx=2)
        ttk.Button(top_bar, text="📊 Riepilogo", command=self.show_project_summary, width=12).pack(side="left", padx=2)
        ttk.Button(top_bar, text="➕ Aggiungi", command=self.add_material_dialog, style="Accent.TButton", width=12).pack(side="left", padx=2)
        ttk.Checkbutton(top_bar, text="Sempre in Primo Piano", variable=self.always_on_top_var, command=self.toggle_always_on_top).pack(side="right", padx=5)
        ttk.Button(top_bar, text="⚙️ Impostazioni", command=self.show_settings, width=14).pack(side="right", padx=2)
        
        filter_bar = ttk.Frame(self.root, padding=5)
        filter_bar.pack(fill="x")
        ttk.Label(filter_bar, text="🔍 Cerca: ").pack(side="left", padx=2)
        self.search_entry = ttk.Entry(filter_bar, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left", padx=5)
        ttk.Checkbutton(filter_bar, text="Nascondi completati", variable=self.hide_completed, command=self.refresh_treeview).pack(side="left", padx=10)
        ttk.Checkbutton(filter_bar, text="Solo risorse mancanti", variable=self.show_missing_only, command=self.refresh_treeview).pack(side="left", padx=10)
        ttk.Button(filter_bar, text="📂 Espandi tutto", command=lambda: self.toggle_all_folders(True)).pack(side="right", padx=2)
        ttk.Button(filter_bar, text="📁 Riduci tutto", command=lambda: self.toggle_all_folders(False)).pack(side="right", padx=2)
        
        self.pane = ttk.Panedwindow(self.root, orient="horizontal")
        self.pane.pack(fill="both", expand=True, padx=5, pady=5)
        tree_frame = ttk.Frame(self.pane)
        self.pane.add(tree_frame, weight=4)
        
        self.tree = ttk.Treeview(tree_frame, columns=("Richiesto", "Mancante", "Disponibile"), show="tree headings")
        self.tree.heading("#0", text="Struttura Categorie / Materiale", anchor="w")
        self.tree.heading("Richiesto", text="Totale Richiesto")
        self.tree.heading("Mancante", text="Mancante")
        self.tree.heading("Disponibile", text="Disponibile")
        self.tree.column("#0", width=450, anchor="w")
        self.tree.column("Richiesto", width=160, anchor="center")
        self.tree.column("Mancante", width=160, anchor="center")
        self.tree.column("Disponibile", width=160, anchor="center")
        
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        self.slider_panel = ttk.LabelFrame(self.pane, text=" Regolazione Rapida Qtà ", padding=10)
        self.pane.add(self.slider_panel, weight=1)
        self.slider_panel.pack_forget()
        self.slider_title_lbl = ttk.Label(self.slider_panel, text="Blocco Selezionato", font=("Segoe UI", 10, "bold"), wraplength=180)
        self.slider_title_lbl.pack(fill="x", pady=(0, 10))
        self.quick_scale = ttk.Scale(self.slider_panel, from_=0, to=100, orient="horizontal", command=self._on_slider_scroll)
        self.quick_scale.pack(fill="x", pady=5)
        self.slider_val_lbl = ttk.Label(self.slider_panel, text="0 / 0", font=("Consolas", 11, "bold"), anchor="center")
        self.slider_val_lbl.pack(fill="x", pady=5)
        
        if hasattr(self.root, 'drop_target_register'):
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self._on_file_drop)
            
        self.bottom_bar = ttk.Frame(self.root, padding=2)
        self.bottom_bar.pack(fill="x", side="bottom")
        self.progress_bar = ModernProgressBar(self.bottom_bar)
        self.progress_bar.pack(fill="x", pady=2)
        
        self.pagination_frame = ttk.Frame(self.bottom_bar)
        self.pagination_frame.pack(fill="x", pady=2)
        self.btn_prev_page = ttk.Button(self.pagination_frame, text="◀ Precedente", command=self._prev_page, width=15)
        self.btn_prev_page.pack(side="left", padx=10)
        self.btn_next_page = ttk.Button(self.pagination_frame, text="Successiva ▶", command=self._next_page, width=15)
        self.btn_next_page.pack(side="right", padx=10)
        self.page_label = ttk.Label(self.pagination_frame, text="Pagina 1/1", anchor="center")
        self.page_label.pack(fill="x", expand=True, pady=4)

    def _on_search_change(self):
        self.current_page = 0
        self.refresh_treeview()

    def _hide_slider(self):
        if self.slider_panel.winfo_ismapped(): self.slider_panel.pack_forget()

    def _on_tree_select(self, event):
        if self._ignore_select: return
        sel = self.tree.selection()
        if not sel:
            self._hide_slider()
            return
        item_id = sel[0]
        tags = self.tree.item(item_id, "tags")
        if any(t in tags for t in ('completed', 'partial', 'unstarted')):
            nome = self.tree.item(item_id, "text").strip().replace(" ✓", "")
            for cat_items in self.data_manager.data.values():
                if nome in cat_items:
                    mat = cat_items[nome]
                    self.slider_title_lbl.configure(text=nome)
                    self.quick_scale.configure(to=max(1, mat.total))
                    self._ignore_select = True
                    self.quick_scale.set(mat.available)
                    self._ignore_select = False
                    self.slider_val_lbl.configure(text=f"{mat.available} / {mat.total}")
                    if not self.slider_panel.winfo_ismapped():
                        self.slider_panel.pack(side="right", fill="both", before=self.tree.master)
                    return
        self._hide_slider()

    def _on_slider_scroll(self, value):
        if self._ignore_select: return
        sel = self.tree.selection()
        if not sel: return
        item_id = sel[0]
        new_val = int(float(value))
        nome = self.tree.item(item_id, "text").strip().replace(" ✓", "")
        for cat_items in self.data_manager.data.values():
            if nome in cat_items:
                mat = cat_items[nome]
                new_val = max(0, min(mat.total, new_val))
                self.slider_val_lbl.configure(text=f"{new_val} / {mat.total}")
                self._update_material_amount(item_id, new_val)
                break

    def _create_context_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="white", bd=0)
        self.menu.add_command(label="📝 Modifica Materiale", command=self.edit_material)
        self.menu.add_command(label="🗑️ Elimina", command=self.delete_selected)
        self.menu.add_separator()
        self.menu.add_command(label="📋 Copia Nome", command=self.copy_material_name)
        
        self.cat_menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="white", bd=0)
        self.cat_menu.add_command(label="✏️ Rinomina Sottocategoria", command=self.rename_category)
        self.cat_menu.add_command(label="👁️ Ignora/Riattiva", command=self.toggle_ignore)
        self.cat_menu.add_separator()
        self.cat_menu.add_command(label="🗑️ Elimina Sottocategoria", command=self.delete_category)

        self.main_menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="white", bd=0)
        self.main_menu.add_command(label="➕ Aggiungi Sottocartella / Materiale", command=self.add_material_to_main)
        self.main_menu.add_command(label="📥 Importa File in questo Gruppo", command=self.import_file_to_main)
        self.main_menu.add_separator()
        self.main_menu.add_command(label="✏️ Rinomina Intero Gruppo", command=self.rename_category)
        self.main_menu.add_command(label="🗑️ Elimina Intero Gruppo", command=self.delete_category)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return
        self.tree.selection_set(item)
        if str(item).startswith("MAIN__"): self.main_menu.post(event.x_root, event.y_root)
        elif str(item).startswith("CAT__"): self.cat_menu.post(event.x_root, event.y_root)
        else: self.menu.post(event.x_root, event.y_root)

    def refresh_treeview(self):
        self._hide_slider()
        search = self.search_var.get().lower()
        hide_comp = self.hide_completed.get()
        missing_only = self.show_missing_only.get()
        is_searching = len(search) > 0
        
        self.tree.delete(*self.tree.get_children())
        self.tree["displaycolumns"] = [c for c, v in self.column_visibility.items() if v.get()]

        all_filtered_mats = []
        for cat_key, items in self.data_manager.data.items():
            is_cat_ignored = self.data_manager.is_ignored(cat_key)
            if is_searching and is_cat_ignored: continue
            main_cat, sub_cat = cat_key.split(" // ", 1) if " // " in cat_key else (cat_key, "Generale")
            for name, mat in items.items():
                if is_searching and (search not in name.lower() and search not in sub_cat.lower() and search not in main_cat.lower()): continue
                if (hide_comp or missing_only) and mat.missing == 0: continue
                all_filtered_mats.append((main_cat, sub_cat, cat_key, name, mat, is_cat_ignored))

        all_filtered_mats.sort(key=lambda x: (x[0], x[1], x[3]))
        total_items = len(all_filtered_mats)

        if is_searching:
            items_to_show = all_filtered_mats
            self.pagination_frame.pack_forget() 
        else:
            self.pagination_frame.pack(side="bottom", fill="x")
            max_pages = max(0, (total_items - 1) // self.items_per_page) if total_items > 0 else 0
            if self.current_page > max_pages: self.current_page = max_pages
            start_idx = self.current_page * self.items_per_page
            end_idx = start_idx + self.items_per_page
            items_to_show = all_filtered_mats[start_idx:end_idx]
            if total_items == 0:
                self.page_label.config(text="Nessun elemento trovato")
            else:
                self.page_label.config(text=f"Elementi {start_idx+1}-{min(end_idx, total_items)} di {total_items}  (Pagina {self.current_page+1}/{max_pages+1})")
            self.btn_prev_page.config(state="normal" if self.current_page > 0 else "disabled")
            self.btn_next_page.config(state="normal" if end_idx < total_items else "disabled")

        inserted_main_nodes, inserted_sub_nodes = {}, {}
        for main_cat, sub_cat, cat_key, name, mat, is_cat_ignored in items_to_show:
            main_iid, cat_iid = f"MAIN__{main_cat}", f"CAT__{cat_key}"
            if main_iid not in inserted_main_nodes:
                self.tree.insert("", "end", iid=main_iid, text=main_cat, tags=('main_category',), open=True)
                inserted_main_nodes[main_iid] = True
            if cat_iid not in inserted_sub_nodes:
                cat_text = f"{sub_cat} (Ignorato)" if is_cat_ignored else sub_cat
                self.tree.insert(main_iid, "end", iid=cat_iid, text=cat_text, tags=('category_ignored' if is_cat_ignored else 'category',), open=True)
                inserted_sub_nodes[cat_iid] = True
            self._insert_material_row(cat_iid, name, mat, is_cat_ignored)

        self.tree.tag_configure('main_category', font=("Segoe UI Variable Display", 11, "bold"), background="#2b2d31")
        self.tree.tag_configure('category', font=("Segoe UI Variable Text", 10, "bold"), background="#383a40")
        self.tree.tag_configure('category_ignored', font=("Segoe UI Variable Text", 10, "italic"), foreground=TEXT_MUTED)
        self.tree.tag_configure('completed', foreground=GREEN)
        self.tree.tag_configure('partial', foreground=YELLOW)
        self.tree.tag_configure('unstarted', foreground=TEXT_MAIN)
        self.tree.tag_configure('ignored_item', foreground=TEXT_MUTED)
        self.update_global_progress()

    def _prev_page(self):
        if self.current_page > 0: self.current_page -= 1; self.refresh_treeview()

    def _next_page(self):
        self.current_page += 1; self.refresh_treeview()

    def _insert_material_row(self, parent_iid, name, mat, is_cat_ignored):
        is_completed = mat.total > 0 and mat.available >= mat.total
        status_tag = 'ignored_item' if is_cat_ignored else ('completed' if is_completed else 'partial' if mat.available > 0 else 'unstarted')
        checkmark = " ✓" if (is_completed and not is_cat_ignored) else ""
        insert_params = {
            "text": f" {name}{checkmark}",
            "values": (format_smart_minecraft(mat.total), format_smart_minecraft(mat.missing), format_smart_minecraft(mat.available)),
            "tags": (status_tag,)
        }
        icon_image = self.texture_manager.get_icon(name)
        if icon_image: insert_params["image"] = icon_image
        self.tree.insert(parent_iid, "end", **insert_params)

    def _bind_shortcuts(self):
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.root.bind("<plus>", lambda e: self._quick_math(1))
        self.root.bind("<KP_Add>", lambda e: self._quick_math(1))
        self.root.bind("<minus>", lambda e: self._quick_math(-1))
        self.root.bind("<KP_Subtract>", lambda e: self._quick_math(-1))
        self.root.bind("<Shift-plus>", lambda e: self._quick_math(64))
        self.root.bind("<Shift-KP_Add>", lambda e: self._quick_math(64))
        self.root.bind("<Shift-minus>", lambda e: self._quick_math(-64))
        self.root.bind("<Shift-KP_Subtract>", lambda e: self._quick_math(-64))
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set() if hasattr(self, 'search_entry') else None)
        self.root.bind("c", lambda e: self.copy_material_name())

    def _quick_math(self, delta):
        selected = self.tree.selection()
        if not selected: return
        for item_id in selected:
            tags = self.tree.item(item_id, "tags")
            if any(t in tags for t in ('completed', 'partial', 'unstarted')):
                nome = self.tree.item(item_id, "text").strip().replace(" ✓", "")
                for cat_items in self.data_manager.data.values():
                    if nome in cat_items:
                        mat = cat_items[nome]
                        new_val = max(0, min(mat.total, mat.available + delta))
                        self._update_material_amount(item_id, new_val)
                        if item_id == selected[0] and self.slider_panel.winfo_ismapped():
                            self.quick_scale.set(new_val)
                            self.slider_val_lbl.configure(text=f"{new_val} / {mat.total}")
                        break
        self._ignore_select = True
        self.tree.selection_set(selected)
        self.tree.focus(selected[0])
        self._ignore_select = False
        return "break"

    def _update_material_amount(self, item_id, new_val):
        nome = self.tree.item(item_id, "text").strip().replace(" ✓", "")
        for cat_key, items in self.data_manager.data.items():
            if nome in items:
                mat = items[nome]
                mat.available = new_val
                is_completed = mat.available >= mat.total
                checkmark = " ✓" if is_completed else ""
                status_tag = 'completed' if is_completed else 'partial' if mat.available > 0 else 'unstarted'
                self.tree.item(item_id, text=f" {nome}{checkmark}", 
                               values=(format_smart_minecraft(mat.total), format_smart_minecraft(mat.missing), format_smart_minecraft(mat.available)),
                               tags=(status_tag,))
                break
        self.update_global_progress()

    def update_global_progress(self):
        total_g, avail_g = 0, 0
        for cat_key, items in self.data_manager.data.items():
            if not self.data_manager.is_ignored(cat_key):
                for m in items.values():
                    total_g += m.total
                    avail_g += m.available
        perc = (avail_g / total_g * 100) if total_g > 0 else 0
        self.progress_bar.update_bar(avail_g, total_g, f"PROGRESSO TOTALE: {perc:.1f}% ({avail_g} / {total_g})")

    def add_material_dialog(self):
        cats = sorted(list(set(k.split(" // ")[0] for k in self.data_manager.data.keys())))
        d = NewMaterialDialog(self.root, "Nuovo Materiale", cats)
        if d.result:
            cat_key = f"{d.result['main_category']} // {d.result['sub_category']}"
            if cat_key not in self.data_manager.data: self.data_manager.data[cat_key] = {}
            self.data_manager.data[cat_key][d.result['name']] = Material(total=d.result['total'], available=d.result['available'])
            self.refresh_treeview()

    def add_material_to_main(self):
        sel = self.tree.focus()
        if not sel or not str(sel).startswith("MAIN__"): return
        main_cat = str(sel).split("MAIN__", 1)[1]
        cats = sorted(list(set(k.split(" // ")[0] for k in self.data_manager.data.keys())))
        d = NewMaterialDialog(self.root, f"Nuova Sottocartella in: {main_cat}", cats, {"main_category": main_cat})
        if d.result:
            cat_key = f"{d.result['main_category']} // {d.result['sub_category']}"
            if cat_key not in self.data_manager.data: self.data_manager.data[cat_key] = {}
            self.data_manager.data[cat_key][d.result['name']] = Material(total=d.result['total'], available=d.result['available'])
            self.refresh_treeview()

    def edit_material(self):
        sel = self.tree.focus()
        if not sel or any(str(sel).startswith(p) for p in ("MAIN__", "CAT__", "I0")): return
        nome = self.tree.item(sel, "text").strip().replace(" ✓", "")
        for cat_key, items in self.data_manager.data.items():
            if nome in items:
                mat = items[nome]
                main_c, sub_c = cat_key.split(" // ", 1) if " // " in cat_key else (cat_key, "Generale")
                cats = sorted(list(set(k.split(" // ")[0] for k in self.data_manager.data.keys())))
                d = NewMaterialDialog(self.root, "Modifica Materiale", cats, 
                                     {"main_category": main_c, "sub_category": sub_c, "name": nome, "total": mat.total, "available": mat.available})
                if d.result:
                    del items[nome]
                    new_cat = f"{d.result['main_category']} // {d.result['sub_category']}"
                    if new_cat not in self.data_manager.data: self.data_manager.data[new_cat] = {}
                    self.data_manager.data[new_cat][d.result['name']] = Material(total=d.result['total'], available=d.result['available'])
                    self.refresh_treeview()
                break

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        if modern_askyesno(self.root, "Elimina", f"Sei sicuro di voler eliminare {len(selected)} elementi?"):
            for sel in selected:
                if str(sel).startswith("CAT__"):
                    cat_key = str(sel).split("CAT__", 1)[1]
                    if cat_key in self.data_manager.data: del self.data_manager.data[cat_key]
                elif str(sel).startswith("MAIN__"):
                    main_cat = str(sel).split("MAIN__", 1)[1]
                    keys_to_del = [k for k in self.data_manager.data.keys() if k.startswith(f"{main_cat} // ") or k == main_cat]
                    for k in keys_to_del: del self.data_manager.data[k]
                else:
                    nome = self.tree.item(sel, "text").strip().replace(" ✓", "")
                    for items in self.data_manager.data.values():
                        if nome in items:
                            del items[nome]
                            break
            self.refresh_treeview()

    def toggle_ignore(self):
        sel = self.tree.focus()
        if not sel or not str(sel).startswith("CAT__"): return
        cat_key = str(sel).split("CAT__", 1)[1]
        self.data_manager.toggle_ignore_category(cat_key)
        self.refresh_treeview()

    def toggle_all_folders(self, force_state=None):
        all_items = self.tree.get_children()
        if not all_items: return
        state = force_state if force_state is not None else not any(self.tree.item(i, "open") for i in all_items)
        for i in all_items:
            self.tree.item(i, open=state)
            for child in self.tree.get_children(i): self.tree.item(child, open=state)

    def show_project_summary(self):
        ProjectSummaryDialog(self.root, self.data_manager.data, self.data_manager.ignored_categories)

    def import_file_dialog(self):
        filepaths = filedialog.askopenfilenames(initialdir=self.import_directory, title="Seleziona file (.json / .txt)", filetypes=[("Material Files", "*.json;*.txt")])
        if not filepaths: return
        self.import_directory = os.path.dirname(filepaths[0])
        for filepath in filepaths:
            filename = os.path.basename(filepath)
            proj_name = os.path.splitext(filename)[0]
            if filepath.endswith(".json"): count = self.data_manager.import_from_json(filepath, proj_name)
            else: count = self.data_manager.import_from_txt(filepath, proj_name)
            if count > 0: modern_messagebox(self.root, "Successo", f"Importato: {filename}\nMateriali analizzati: {count}", "success")
            else: modern_messagebox(self.root, "Errore", f"Impossibile leggere materiali in: {filename}", "error")
        self.data_manager.save_data()
        self.current_page = 0
        self.refresh_treeview()

    def import_file_to_main(self):
        sel = self.tree.focus()
        if not sel or not str(sel).startswith("MAIN__"): return
        main_cat = str(sel).split("MAIN__", 1)[1]
        path = filedialog.askopenfilename(initialdir=self.import_directory, filetypes=[("Material Files", "*.txt;*.json")])
        if path:
            suggested_sub = os.path.splitext(os.path.basename(path))[0].title()
            sub_cat = simpledialog.askstring("Importa in " + main_cat, f"Nome della nuova Sottocartella per '{os.path.basename(path)}':", initialvalue=suggested_sub)
            if sub_cat:
                full_cat = f"{main_cat} // {sub_cat.strip()}"
                count = self.data_manager.import_from_json(path, full_cat) if path.endswith(".json") else self.data_manager.import_from_txt(path, full_cat)
                if count > 0:
                    modern_messagebox(self.root, "Importazione", f"Importati {count} materiali nella categoria '{full_cat}'.", "success")
                    self.current_page = 0
                    self.refresh_treeview()
                else: 
                    modern_messagebox(self.root, "Errore", "Nessun materiale valido trovato nel file.", "error")

    def import_from_clipboard(self):
        cats = sorted(list(set(k.split(" // ")[0] for k in self.data_manager.data.keys())))
        d = PasteImportDialog(self.root, cats)
        if d.result:
            count = self.data_manager.import_from_string(d.result[1], d.result[0])
            if count > 0:
                modern_messagebox(self.root, "Successo", f"Importati {count} materiali.", "success")
                self.refresh_treeview()

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV file", "*.csv")])
        if filepath and self.data_manager.export_to_csv(filepath):
            modern_messagebox(self.root, "Successo", "Esportato con successo in CSV.", "success")

    def copy_material_name(self):
        sel = self.tree.selection()
        if not sel: return
        names = [self.tree.item(s, "text").strip().replace(" ✓", "") for s in sel if not self.tree.item(s, "text").strip().startswith(("MAIN__", "CAT__"))]
        if names:
            self.root.clipboard_clear()
            self.root.clipboard_append(", ".join(names))

    def rename_category(self):
        sel = self.tree.focus()
        if not sel: return
        if str(sel).startswith("MAIN__"):
            old_main = str(sel).split("MAIN__", 1)[1]
            new_main = simpledialog.askstring("Rinomina", "Nuovo nome Categoria Principale:", initialvalue=old_main)
            if new_main and new_main != old_main:
                new_main = new_main.strip().title()
                for k in [k for k in self.data_manager.data.keys() if k == old_main or k.startswith(f"{old_main} // ")]:
                    new_key = f"{new_main} // {k.split(' // ', 1)[1]}" if " // " in k else f"{new_main} // Generale"
                    self.data_manager.data[new_key] = self.data_manager.data.pop(k)
                self.refresh_treeview()
        elif str(sel).startswith("CAT__"):
            old_cat = str(sel).split("CAT__", 1)[1]
            old_sub = old_cat.split(" // ", 1)[1] if " // " in old_cat else old_cat
            new_sub = simpledialog.askstring("Rinomina", "Nuovo nome Sottocategoria:", initialvalue=old_sub)
            if new_sub and new_sub != old_sub:
                new_sub = new_sub.strip().title()
                new_cat = f"{old_cat.split(' // ', 1)[0]} // {new_sub}" if " // " in old_cat else new_sub
                self.data_manager.data[new_cat] = self.data_manager.data.pop(old_cat)
                self.refresh_treeview()

    def delete_category(self):
        sel = self.tree.focus()
        if not sel: return
        if str(sel).startswith("CAT__"):
            cat_key = str(sel).split("CAT__", 1)[1]
            if modern_askyesno(self.root, "Elimina Categoria", f"Eliminare definitivamente '{cat_key}'?"):
                del self.data_manager.data[cat_key]
                self.refresh_treeview()
        elif str(sel).startswith("MAIN__"):
            main_cat = str(sel).split("MAIN__", 1)[1]
            if modern_askyesno(self.root, "Elimina Gruppo", f"Eliminare tutte le sottocategorie di '{main_cat}'?"):
                keys = [k for k in self.data_manager.data.keys() if k.startswith(f"{main_cat} // ") or k == main_cat]
                for k in keys: del self.data_manager.data[k]
                self.refresh_treeview()

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def update_window_title(self):
        self.root.title(f"Material Dreamer - {os.path.basename(self.save_directory) if self.save_directory else 'Nuovo Progetto'}")

    def mostra_anteprima_importazione(self, nome_file, conteggio_blocchi):
        d = Toplevel(self.root)
        d.title(f"Anteprima: {nome_file}")
        d.geometry("600x550")
        pywinstyles.apply_style(d, "dark")
        d.transient(self.root)
        d.grab_set()
        frame = ttk.Frame(d, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="✨ Anteprima Materiali Trovati", font=("Segoe UI", 14, "bold"), foreground="#f0b232").pack(pady=(0, 5))
        tabella = ttk.Treeview(frame, columns=("Blocco", "Quantità"), show="headings", height=10)
        tabella.heading("Blocco", text="Nome Materiale")
        tabella.heading("Quantità", text="Quantità Totale")
        tabella.column("Blocco", width=300, anchor="w")
        tabella.column("Quantità", width=150, anchor="center")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tabella.yview)
        tabella.configure(yscrollcommand=scrollbar.set)
        tabella_frame = ttk.Frame(frame)
        tabella_frame.pack(fill="both", expand=True, pady=5)
        tabella.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        totale_blocchi = 0
        for blocco, quantita in sorted(conteggio_blocchi.items(), key=lambda x: x[1], reverse=True):
            tabella.insert("", "end", values=(blocco.title(), format_smart_minecraft(quantita)))
            totale_blocchi += quantita
        ttk.Label(frame, text=f"Totale complessivo: {totale_blocchi}", font=("Segoe UI", 10, "bold")).pack(anchor="e", pady=5)
        ttk.Label(frame, text="Scegli o scrivi la Categoria:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 5))
        cb_categoria = ttk.Combobox(frame, values=self.data_manager.get_all_categories(), font=("Segoe UI", 11))
        cb_categoria.set(nome_file)
        cb_categoria.pack(fill="x", pady=(0, 15))
        def conferma():
            categoria = cb_categoria.get().strip()
            if not categoria: return
            cat_data = self.data_manager.data.setdefault(categoria, {})
            for nome_blocco, quantita in conteggio_blocchi.items():
                nome_formattato = nome_blocco.replace("_", " ").title()
                if nome_formattato in cat_data: cat_data[nome_formattato].total += quantita
                else: cat_data[nome_formattato] = Material(total=quantita, available=0)
            self.data_manager.save_data()
            d.destroy()
            self.refresh_treeview()
        ttk.Button(frame, text="✅ Conferma Importazione", command=conferma, style="Accent.TButton").pack(fill="x", pady=5)

    def _on_file_drop(self, event):
        percorso = event.data.strip('{}')
        estensione = percorso.lower().split('.')[-1]
        if estensione in ['txt', 'json']:
            nome_file = os.path.splitext(os.path.basename(percorso))[0]
            temp_cat = "__temp_preview__"
            if estensione == 'json': count = self.data_manager.import_from_json(percorso, temp_cat)
            else: count = self.data_manager.import_from_txt(percorso, temp_cat)
            if count <= 0 or temp_cat not in self.data_manager.data:
                messagebox.showwarning("File Vuoto", "Non ho trovato materiali validi in questo file.")
                if temp_cat in self.data_manager.data: del self.data_manager.data[temp_cat]
                return
            conteggio = {nome: mat.total for nome, mat in self.data_manager.data[temp_cat].items()}
            del self.data_manager.data[temp_cat]
            self.mostra_anteprima_importazione(nome_file, conteggio)
            return
        if estensione == 'litematic':
            messagebox.showwarning("Attenzione", "Ricorda che Litematica bugga i file diretti! Usa l'esportazione in .TXT o .JSON.")
            return

    def show_settings(self):
        d = CustomDialogBase(self.root, "Impostazioni", "500x300")
        frame = ttk.Frame(d, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Cartella Salvataggi:").pack(anchor="w")
        sv = ttk.Entry(frame)
        sv.pack(fill="x", pady=(0,15))
        sv.insert(0, self.save_directory)
        ttk.Label(frame, text="Cartella Importazione Predefinita:").pack(anchor="w")
        iv = ttk.Entry(frame)
        iv.pack(fill="x", pady=(0,15))
        iv.insert(0, self.import_directory)
        def apply():
            self.save_directory, self.import_directory = sv.get(), iv.get()
            self.data_filepath = os.path.join(self.save_directory, "construction_materials.json")
            self.data_manager.set_filepath(self.data_filepath)
            save_config({"save_directory": self.save_directory, "import_directory": self.import_directory})
            self.update_window_title()
            self.refresh_treeview()
            d.destroy()
        ttk.Button(frame, text="Salva Impostazioni", command=apply, style="Accent.TButton").pack(side="right")

    def _on_close(self):
        self.data_manager.save_data()
        config = load_config()
        config["save_directory"] = self.save_directory
        config["import_directory"] = self.import_directory
        config["window_geometry"] = self.root.geometry()
        config["column_visibility"] = {k: v.get() for k, v in self.column_visibility.items()}
        save_config(config)
        self.root.destroy()