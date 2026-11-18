import sys
import xml.etree.ElementTree as ET

MINIMO_LINHAS = 85.0
MINIMO_BRANCHES = 80.0

raiz = ET.parse("coverage.xml").getroot()
linhas = float(raiz.get("line-rate")) * 100
branches = float(raiz.get("branch-rate")) * 100

print(f"Cobertura de linhas: {linhas:.1f}% (mínimo {MINIMO_LINHAS}%)")
print(f"Cobertura de branches: {branches:.1f}% (mínimo {MINIMO_BRANCHES}%)")

if linhas < MINIMO_LINHAS or branches < MINIMO_BRANCHES:
    print("FALHA: cobertura abaixo do mínimo exigido")
    sys.exit(1)

print("OK: cobertura dentro da meta")