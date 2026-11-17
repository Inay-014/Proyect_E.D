"""Revisa motor/*.py buscando lo PROHIBIDO por el enunciado. Corre: python revisar_prohibidos.py

Detecta con certeza: dict y set (constructores, literales y comprensiones, incluidos los
literales con contenido mediante el AST), sorted(,
.sort(, min(, max(, .index(, .count(, bisect/heapq/collections/functools y cualquier
import que no sea csv, time o random.
Lo que NO puede detectar solo: 'x in lista' (permitido sobre str y sobre la TablaHash
propia; prohibido sobre una lista). Por eso imprime esas lineas para revisarlas a mano.
AVISO aparte: los 'return {...}' de viaje() y simular_fila() son el FORMATO de salida;
confirmen con el enunciado si debe ser otro tipo.
"""
import glob
import ast
import os
import re

RAIZ = os.path.dirname(os.path.abspath(__file__))
PERMITIDOS = {"csv", "time", "random"}
PATRONES = [r"\bsorted\s*\(", r"\.sort\s*\(", r"\bmin\s*\(", r"\bmax\s*\(",
            r"\.index\s*\(", r"\.count\s*\(", r"\bdict\s*\(", r"\bset\s*\(", r"\bfrozenset\s*\("]
SALIDAS = []

errores = 0
revisar = []
for archivo in sorted(glob.glob(os.path.join(RAIZ, "motor", "*.py"))):
    nombre = os.path.basename(archivo)
    with open(archivo, encoding="utf-8") as f:
        contenido = f.read()
        try:
            arbol = ast.parse(contenido, filename=nombre)
            for nodo in ast.walk(arbol):
                if isinstance(nodo, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp)):
                    print(f"PROHIBIDO  {nombre}:{nodo.lineno}: literal o comprension de dict/set")
                    errores += 1
        except SyntaxError as e:
            print(f"ERROR DE SINTAXIS  {nombre}:{e.lineno}: {e.msg}")
            errores += 1
        for n, linea in enumerate(contenido.splitlines(), 1):
            s = linea.strip()
            if s.startswith("#"):
                continue
            if re.match(r"return\s*\{", s) or (SALIDAS and SALIDAS[-1][2] and not s.startswith(("def ", "class "))  and re.match(r'"\w+":', s)):
                SALIDAS.append((nombre, n, True))
            elif SALIDAS and SALIDAS[-1][2]:
                SALIDAS.append((nombre, n, False))
            for p in PATRONES:
                if re.search(p, linea):
                    print(f"PROHIBIDO  {nombre}:{n}: {s}")
                    errores += 1
            m = re.match(r"\s*(?:from|import)\s+([\w\.]+)", linea)
            if m and not m.group(1).startswith(".") and m.group(1).split(".")[0] not in PERMITIDOS:
                print(f"IMPORT NO PERMITIDO  {nombre}:{n}: {s}")
                errores += 1
            if re.search(r"\bin\b", linea) and not re.match(r"\s*for\s", linea) \
                    and not s.startswith(('"', "'")) and "import" not in s:
                revisar.append(f"{nombre}:{n}: {s}")

print("\nLineas con 'in' para revisar a mano (debe ser str o TablaHash propia, NUNCA una lista):")
for r in revisar:
    print("  ", r)
salidas = [x for x in SALIDAS if x[2]]
if salidas:
    archivos = []
    for x in salidas:
        if x[0] not in archivos:
            archivos.append(x[0])
    print("\nAVISO: valores de retorno escritos como {...} en:", ", ".join(archivos),
          "-> confirmar el formato con el enunciado.")
print("\nResultado:", "SIN prohibidos detectables" if errores == 0 else f"{errores} problema(s)")
