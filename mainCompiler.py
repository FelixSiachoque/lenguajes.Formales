import sys
import os
from AnalisisLexico import analisis
from Sintactico import Sintactico

EXTENSION = ".bip"
def convertir_indentacion(lineas):
    """
    Toma líneas de código indentadas (estilo Python con ':') 
    y las traduce a la sintaxis con llaves '{}' que espera el Sintactico.
    """
    resultado = []
    indents = [0]

    for linea in lineas:
        if not linea.strip():
            continue
        indentacion = len(linea) - len(linea.lstrip(' \t'))
        contenido = linea.strip()

        while indentacion < indents[-1]:
            indents.pop()
            resultado.append('}')
        if indentacion > indents[-1]:
            indents.append(indentacion)
        if contenido.endswith(':'):
            resultado.append(contenido[:-1].rstrip() + ' {')
        else:
            resultado.append(contenido)

    while len(indents) > 1:
        indents.pop()
        resultado.append('}')
    return '\n'.join(resultado)


def ejecutar_codigo(texto, entorno=None):
    """Preprocesa la indentación, tokeniza y ejecuta el código."""
    if entorno is None:
        entorno = {}

    texto = texto.strip()
    if not texto:
        return entorno

    try:
        lineas = texto.splitlines()
        texto_procesado = convertir_indentacion(lineas)

        tokens = analisis(texto_procesado)
        print("Tokens:", tokens)

        analizador = Sintactico(tokens, variables=entorno)
        entorno_actualizado = analizador.analisisPrograma()
        print("Resultado (entorno):", entorno_actualizado)
        return entorno_actualizado

    except (SyntaxError, ValueError, NameError, TypeError) as error:
        print(f"Error de ejecución/sintaxis: {error}")
        return entorno


def ejecutar_archivo(ruta):
    """Lee un archivo de código con la extensión adecuada y lo ejecuta."""
    if not os.path.exists(ruta):
        print(f"Error: El archivo '{ruta}' no existe.")
        return

    if not ruta.lower().endswith(EXTENSION):
        print(f"Error: El archivo debe tener la extensión '{EXTENSION}'")
        return

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
    except Exception as error:
        print(f"Error leyendo el archivo: {error}")
        return

    print(f"--- Ejecutando archivo: {ruta} ---")
    ejecutar_codigo(contenido)


def modo_interactivo():
    """Modo consola REPL."""
    print("====================================")
    print(f" BIENVENIDO AL COMPILADOR ({EXTENSION})")
    print(" Escribe tu código o 'CERRAR' para salir.")
    print("====================================")

    entorno_global = {}

    while True:
        try:
            linea = input("BIP> ")
            if linea.strip().upper() == "CERRAR":
                print("Programa terminado.")
                break

            entorno_global = ejecutar_codigo(linea, entorno=entorno_global)

        except (KeyboardInterrupt, EOFError):
            print("\nPrograma terminado.")
            break


def main():
    if len(sys.argv) == 1:
        modo_interactivo()
        return

    if sys.argv[1] in ("--help", "-h"):
        print(f"Uso: python mainCompiler.py [archivo{EXTENSION}]")
        return

    if len(sys.argv) == 2:
        ejecutar_archivo(sys.argv[1])
        return

    print("Error: Cantidad inválida de argumentos.")


if __name__ == "__main__":
    main()