# main.pyw
import sys
import os

# Permette a Python di trovare le nostre nuove librerie 'core' e 'ui'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.dependencies import check_and_install_dependencies

def main():
    # 1. Controlla e installa le librerie prima di fare qualsiasi altra cosa
    check_and_install_dependencies()
    
    # 2. Importa le librerie grafiche solo dopo l'installazione
    from tkinterdnd2 import TkinterDnD
    from core.config import load_config
    from ui.main_window import MaterialGUI
    
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
    else:
        root.geometry(config["window_geometry"])
        
    root.deiconify()
    root.mainloop()

if __name__ == "__main__":
    main()