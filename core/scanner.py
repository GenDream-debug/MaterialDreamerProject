# core/scanner.py
import re
import json

# Espressione regolare avanzata per catturare il nome del blocco e la sua formula numerica
PATTERN_MATERIALE = re.compile(r'^([a-zA-Z_:\s0-9]+?)[:\-]?\s+([\d\+\-\*\/\(\)\.\s]+(?:sb|stk|stack)?.*)$', re.IGNORECASE)

def eval_math(expression: str) -> int:
    """
    Risolve formule matematiche di Minecraft traducendo espressioni di testo in numeri interi.
    - sb = Shulker Box (1728 blocchi)
    - stk / stack = Stack (64 blocchi)
    Esempio: "1sb + 2stk" diventa: (1 * 1728) + (2 * 64) = 1856
    """
    clean = str(expression).lower().strip().replace("sb", "*1728").replace("stk", "*64").replace("stack", "*64")
    # Consente solo caratteri matematici sicuri per evitare falle di sicurezza nell'eval
    if not re.match(r'^[\d\+\-\*\/\(\)\.\s]+$', clean):
        raise ValueError("Formula non valida")
    try:
        return int(eval(clean, {"__builtins__": None}, {}))
    except Exception:
        raise ValueError("Errore nel calcolo della formula")

def format_minecraft(value: int) -> str:
    """
    Scompone un numero intero di blocchi nel formato testuale di Minecraft.
    Esempio: 1800 diventa -> "1800 (1SB+1^+8)"  [dove ^ indica lo Stack]
    """
    if value < 64:
        return str(value)
    sb, rem = value // 1728, value % 1728
    stk, items = rem // 64, rem % 64
    parts = []
    if sb > 0: parts.append(f"{sb}SB")
    if stk > 0: parts.append(f"{stk}^")
    if items > 0: parts.append(f"{items}")
    return f"{value} ({'+'.join(parts)})"

def analizza_file(filepath: str) -> dict:
    """
    Scansiona un file di testo (.txt) o una lista Litematica (.json).
    Pulisce i nomi dei blocchi (toglie 'minecraft:', converte i trattini in spazi)
    e restituisce un dizionario pulito: { "Nome Blocco": QuantitaTotale }
    """
    conteggio = {}
    
    # 1. GESTIONE FILE JSON (Litematica o esportazioni strutturate)
    if filepath.lower().endswith('.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                dati = json.load(f)
            
            # Gestisce sia liste di oggetti che oggetti singoli
            lista_elementi = dati if isinstance(dati, list) else [dati]
            for x in lista_elementi:
                # Estrae il nome dell'item gestendo diversi formati di esportazione
                n = str(x.get("Item", x.get("name", "")))
                n = n.replace("minecraft:", "").replace("_", " ").strip().title()
                
                # Estrae la quantità associata
                q_raw = x.get("TotalEstimate", x.get("total", x.get("count", 0)))
                try:
                    q = int(q_raw)
                    if n and q > 0:
                        conteggio[n] = conteggio.get(n, 0) + q
                except (ValueError, TypeError):
                    pass
        except Exception:
            raise IOError("Impossibile decodificare il file JSON strutturato.")

    # 2. GESTIONE FILE DI TESTO (.txt grezzi o tabelle incollate)
    else:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    # Pulisce i separatori di tabelle comuni (es. i caratteri pipe '|')
                    line_clean = line.replace('|', ' ').strip()
                    m = PATTERN_MATERIALE.search(line_clean)
                    if m:
                        n = m.group(1).replace("minecraft:", "").replace("_", " ").strip().title()
                        # Salta le righe di intestazione delle tabelle
                        if n.lower() in ['item', 'total', 'missing', 'materiale', 'quantità', 'quantita', 'blocco']:
                            continue
                        try:
                            qty = eval_math(m.group(2))
                            if qty > 0:
                                conteggio[n] = conteggio.get(n, 0) + qty
                        except ValueError:
                            pass
        except Exception:
            raise IOError("Errore durante la lettura del file di testo.")
                            
    return conteggio