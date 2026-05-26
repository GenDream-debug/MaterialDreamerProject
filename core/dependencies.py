# core/dependencies.py
import sys
import os
import subprocess

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