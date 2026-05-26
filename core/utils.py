# core/utils.py
import re

PATTERN_MATERIALE = re.compile(r'^([a-zA-Z_:\s]+?)[:\-]?\s+([\d\+\-\*\/\(\)\.\s]+(?:sb|stk|stack|shulker)?.*)$', re.IGNORECASE)
PATTERN_LITEMATIC_LINE = re.compile(r"\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|")

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