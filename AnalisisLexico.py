from Token import Token
import json
from pathlib import Path


def cargar_reglas():
    ruta = Path(__file__).with_name("reglas.json")
    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


REGLAS = cargar_reglas()
PALABRAS_RESERVADAS = REGLAS["palabras_reservadas"]
OPERADORES_RELACIONALES = REGLAS["operadores_relacionales"]
SIMBOLOS = REGLAS["simbolos"]


def analisis(texto):
    tokens = []
    n = len(texto)
    i = 0

    while i < n:
        caracter = texto[i]

        if caracter.isspace():
            i += 1
            continue

        if caracter.isdigit():
            inicio = i
            while i < n and texto[i].isdigit():
                i += 1

            if i < n and texto[i] == "." and i + 1 < n and texto[i + 1].isdigit():
                i += 1
                while i < n and texto[i].isdigit():
                    i += 1
                tokens.append(Token(texto[inicio:i], "NUMERO_DECIMAL"))
                continue

            tokens.append(Token(texto[inicio:i], "NUMERO"))
            continue
        if caracter == '"':
            inicio = i
            i += 1
            while i < n and texto[i] != '"':
                i += 1
            if i == n:
                raise ValueError("Cadena de texto sin comilla de cierre")
            i += 1
            tokens.append(Token(texto[inicio:i], "Cadena tipo String"))
            continue

        if caracter.isalpha() or caracter == "_":
            inicio = i
            i += 1
            while i < n and (texto[i].isalnum() or texto[i] == "_"):
                i += 1
            palabra = texto[inicio:i]
            tipo = PALABRAS_RESERVADAS.get(palabra, "IDENTIFICADOR")
            tokens.append(Token(palabra, tipo))
            continue

        operador_relacional = texto[i:i + 2]
        if operador_relacional in OPERADORES_RELACIONALES:
            tokens.append(Token(operador_relacional, OPERADORES_RELACIONALES[operador_relacional]))
            i += 2
            continue

        if caracter in OPERADORES_RELACIONALES:
            tokens.append(Token(caracter, OPERADORES_RELACIONALES[caracter]))
            i += 1
            continue

        if caracter in SIMBOLOS:
            tokens.append(Token(caracter, SIMBOLOS[caracter]))
            i += 1
            continue

        raise ValueError(f"Caracter no reconocido: {caracter!r}")

    return tokens


if __name__ == "__main__":
    texto = input("Ingrese el texto a analizar: ")

    print("Texto analizado:")
    print(texto)
    print("\nTokens encontrados:")

    try:
        for token in analisis(texto):
            print(f"Lexema: {token.token:<12} Tipo: {token.valor}")
    except ValueError as error:
        print(f"Error: {error}")