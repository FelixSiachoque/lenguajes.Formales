import json
from pathlib import Path

from AnalisisLexico import analisis


with Path("Proyecto/reglas.json").open(encoding="utf-8") as archivo:
    reglas = json.load(archivo)

lexemas = []
lexemas.extend(reglas["palabras_reservadas"])
lexemas.extend(reglas["operadores_relacionales"])
lexemas.extend(reglas["simbolos"])

texto = " ".join(lexemas)
tokens = analisis(texto)
tipos_obtenidos = {token.valor: token.token for token in tokens}

for lexema, tipo_esperado in reglas["palabras_reservadas"].items():
    assert tipos_obtenidos[lexema] == tipo_esperado
for lexema, tipo_esperado in reglas["operadores_relacionales"].items():
    assert tipos_obtenidos[lexema] == tipo_esperado
for lexema, tipo_esperado in reglas["simbolos"].items():
    assert tipos_obtenidos[lexema] == tipo_esperado

print(f"OK: se probaron {len(lexemas)} reglas del JSON.")
