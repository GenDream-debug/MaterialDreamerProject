# ui/components.py
import tkinter as tk
from tkinter import ttk
import pywinstyles
from core.config import BG_SEC, TEXT_MAIN, BLURPLE, GREEN, RED, YELLOW

def modern_messagebox(parent, title, message, type_msg="info"):
    """Finestra di messaggio moderna e stilizzata."""
    d = tk.Toplevel(parent)
    d.title(title)
    d.geometry("400x180")
    d.resizable(False, False)
    pywinstyles.apply_style(d, "dark")
    d.transient(parent)
    d.grab_set()
    
    frame = ttk.Frame(d, padding=20)
    frame.pack(fill="both", expand=True)
    
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLURPLE}
    color = colors.get(type_msg, TEXT_MAIN)
    
    ttk.Label(frame, text=title.upper(), font=("Segoe UI", 12, "bold"), foreground=color).pack(anchor="w", pady=(0, 10))
    ttk.Label(frame, text=message, font=("Segoe UI", 10), wraplength=360).pack(anchor="w", fill="both", expand=True)
    
    ttk.Button(frame, text="OK", command=d.destroy, width=10).pack(anchor="e", pady=(10, 0))
    parent.wait_window(d)

def modern_askyesno(parent, title, message) -> bool:
    """Finestra di conferma moderna (Sì/No) che restituisce un booleano."""
    d = tk.Toplevel(parent)
    d.title(title)
    d.geometry("400x180")
    d.resizable(False, False)
    pywinstyles.apply_style(d, "dark")
    d.transient(parent)
    d.grab_set()
    
    result = {"value": False}
    
    frame = ttk.Frame(d, padding=20)
    frame.pack(fill="both", expand=True)
    
    ttk.Label(frame, text=title.upper(), font=("Segoe UI", 12, "bold"), foreground=YELLOW).pack(anchor="w", pady=(0, 10))
    ttk.Label(frame, text=message, font=("Segoe UI", 10), wraplength=360).pack(anchor="w", fill="both", expand=True)
    
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(anchor="e", pady=(10, 0))
    
    def on_yes():
        result["value"] = True
        d.destroy()
        
    ttk.Button(btn_frame, text="Annulla", command=d.destroy, width=10).pack(side="right", padx=5)
    ttk.Button(btn_frame, text="Sì", command=on_yes, style="Accent.TButton", width=10).pack(side="right")
    
    parent.wait_window(d)
    return result["value"]

class CustomDialogBase(tk.Toplevel):
    """Base moderna per tutte le finestre di dialogo personalizzate."""
    def __init__(self, parent, title, geometry="450x400"):
        super().__init__(parent)
        self.title(title)
        self.geometry(geometry)
        self.resizable(False, False)
        pywinstyles.apply_style(self, "dark")
        self.transient(parent)
        self.grab_set()

class NewMaterialDialog(CustomDialogBase):
    """Finestra di dialogo avanzata per creare o modificare materiali."""
    def __init__(self, parent, title, categories, initial_data=None):
        super().__init__(parent, title, "450x420")
        self.categories = categories
        self.initial_data = initial_data or {}
        self.result = None
        self._build_ui()
        
    def _build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Gruppo Principale:").pack(anchor="w")
        self.cb_main = ttk.Combobox(frame, values=self.categories)
        self.cb_main.pack(fill="x", pady=(0, 10))
        if "main_category" in self.initial_data:
            self.cb_main.set(self.initial_data["main_category"])
            
        ttk.Label(frame, text="Sottocategoria / Sottocartella:").pack(anchor="w")
        self.ent_sub = ttk.Entry(frame)
        self.ent_sub.pack(fill="x", pady=(0, 10))
        self.ent_sub.insert(0, self.initial_data.get("sub_category", "Generale"))
        
        ttk.Label(frame, text="Nome Blocco / Risorsa:").pack(anchor="w")
        self.ent_name = ttk.Entry(frame)
        self.ent_name.pack(fill="x", pady=(0, 10))
        self.ent_name.insert(0, self.initial_data.get("name", ""))
        
        ttk.Label(frame, text="Quantità Totale Richiesta (Es. 64 o 1stk):").pack(anchor="w")
        self.ent_total = ttk.Entry(frame)
        self.ent_total.pack(fill="x", pady=(0, 10))
        self.ent_total.insert(0, str(self.initial_data.get("total", "")))
        
        ttk.Label(frame, text="Quantità Già Disponibile:").pack(anchor="w")
        self.ent_avail = ttk.Entry(frame)
        self.ent_avail.pack(fill="x", pady=(0, 15))
        self.ent_avail.insert(0, str(self.initial_data.get("available", "0")))
        
        from core.utils import evaluate_math_expression
        
        def salva():
            m = self.cb_main.get().strip().title()
            s = self.ent_sub.get().strip().title()
            n = self.ent_name.get().strip().title()
            if not m or not n: return
            
            try:
                tot_val = evaluate_math_expression(self.ent_total.get())
                av_val = evaluate_math_expression(self.ent_avail.get())
                self.result = {"main_category": m, "sub_category": s or "Generale", "name": n, "total": tot_val, "available": av_val}
                self.destroy()
            except ValueError:
                modern_messagebox(self, "Errore", "Controlla le espressioni numeriche inserite!", "error")
                
        ttk.Button(frame, text="Salva Materiale", command=salva, style="Accent.TButton").pack(fill="x", pady=5)

class PasteImportDialog(CustomDialogBase):
    """Finestra per incollare elenchi testuali direttamente dagli appunti."""
    def __init__(self, parent, categories):
        super().__init__(parent, "Importa da Appunti", "550x450")
        self.categories = categories
        self.result = None
        self._build_ui()
        
    def _build_ui(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Destinazione (Scrivi o seleziona Gruppo):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.cb_cat = ttk.Combobox(frame, values=self.categories)
        self.cb_cat.pack(fill="x", pady=(0, 10))
        if self.categories: self.cb_cat.set(self.categories[0])
        
        ttk.Label(frame, text="Incolla qui le righe (Formato Tabella Litematica):").pack(anchor="w")
        self.txt = tk.Text(frame, bg="#1e1e1e", fg=TEXT_MAIN, insertbackground="white", font=("Consolas", 10))
        self.txt.pack(fill="both", expand=True, pady=(0, 10))
        
        def conferma():
            cat = self.cb_cat.get().strip()
            testo = self.txt.get("1.0", "end").strip()
            if cat and testo:
                self.result = (cat, testo)
                self.destroy()
                
        ttk.Button(frame, text="📋 Elabora ed Importa", command=conferma, style="Accent.TButton").pack(fill="x")

class ProjectSummaryDialog(CustomDialogBase):
    """Finestra riassuntiva globale del progetto."""
    def __init__(self, parent, data, ignored_categories):
        super().__init__(parent, "Riepilogo Totale Risorse", "650x500")
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="📊 Totali Complessivi Materiali (Nodi Attivi)", font=("Segoe UI", 12, "bold"), foreground=BLURPLE).pack(anchor="w", pady=(0, 10))
        
        tree = ttk.Treeview(frame, columns=("Richiesto", "Disponibile", "Mancante"), show="tree headings")
        tree.heading("#0", text="Materiale / Risorsa", anchor="w")
        tree.heading("Richiesto", text="Totale")
        tree.heading("Disponibile", text="Disponibile")
        tree.heading("Mancante", text="Mancante")
        
        tree.column("#0", width=300, anchor="w")
        tree.column("Richiesto", width=100, anchor="center")
        tree.column("Disponibile", width=100, anchor="center")
        tree.column("Mancante", width=100, anchor="center")
        
        from core.database import Material
        from core.utils import format_smart_minecraft
        
        globali = {}
        for cat_key, items in data.items():
            if cat_key in ignored_categories: continue
            for name, mat in items.items():
                if name not in globali: globali[name] = Material(0, 0)
                globali[name].total += mat.total
                globali[name].available += mat.available
                
        for name, mat in sorted(globali.items(), key=lambda x: x[1].missing, reverse=True):
            tag = 'done' if mat.missing == 0 else 'missing'
            tree.insert("", "end", text=f" {name}", values=(
                format_smart_minecraft(mat.total),
                format_smart_minecraft(mat.available),
                format_smart_minecraft(mat.missing)
            ), tags=(tag,))
            
        tree.tag_configure('done', foreground=GREEN)
        tree.tag_configure('missing', foreground=TEXT_MAIN)
        
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

class ModernProgressBar(ttk.Frame):
    """Barra di progresso ad alta visibilità con testo integrato."""
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, height=26, bg=BG_SEC, bd=0, highlightthickness=0)
        self.canvas.pack(fill="x", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._redraw())
        self.avail, self.total, self.text = 0, 0, "PROGRESSO: 0%"
        
    def update_bar(self, avail, total, text):
        self.avail, self.total, self.text = avail, total, text
        self._redraw()
        
    def _redraw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        pct = (self.avail / self.total) if self.total > 0 else 0
        
        # Sfondo della barra di avanzamento dinamica
        self.canvas.create_rectangle(0, 0, int(w * pct), 26, fill="#2a633d" if pct >= 1 else "#3b448a", width=0)
        # Testo centrale
        self.canvas.create_text(w // 2, 13, text=self.text, fill="white", font=("Segoe UI", 10, "bold"), anchor="center")