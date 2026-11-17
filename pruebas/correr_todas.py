"""Corre todas las pruebas, cada requisito como programa aparte: python pruebas/correr_todas.py"""
import os
import subprocess
import sys

aqui = os.path.dirname(os.path.abspath(__file__))
fallos = 0
for nombre in ["prueba_fase1.py"] + ["prueba_r%d.py" % i for i in range(1, 11)] + ["prueba_extra.py", "prueba_nuevas.py"]:
    r = subprocess.run([sys.executable, os.path.join(aqui, nombre)], capture_output=True, text=True)
    salida = (r.stdout.strip().splitlines() or [""])[-1] if r.returncode == 0 else r.stderr.strip().splitlines()[-1]
    print(("OK    " if r.returncode == 0 else "FALLA ") + nombre.ljust(18), salida[:110])
    fallos += r.returncode != 0
print("\nTODO OK" if fallos == 0 else "\n%d prueba(s) fallaron" % fallos)
sys.exit(1 if fallos else 0)
