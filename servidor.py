import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from AnalisisLexico import analisis
from Sintactico import Sintactico
from mainCompiler import convertir_indentacion

BASE = Path(__file__).parent

app = FastAPI(
    title="BIP Language API",
    description="API REST para ejecutar y tokenizar código en lenguaje BIP",
    version="1.1"
)

# Permite que la interfaz funcione aunque se abra desde otro origen
# (por ejemplo, abriendo index.html con doble clic o desde Live Server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodigoRequest(BaseModel):
    codigo: str


LIMITE_CODIGO = 20_000      # caracteres máximos de un programa
LIMITE_SALIDA = 100_000     # caracteres máximos que puede imprimir
LIMITE_TAMANO = 100_000     # largo máximo de una cadena o lista


class SintacticoLimitado(Sintactico):
    """Igual que Sintactico, pero con límites para que nadie pueda tumbar el servidor
    (ciclos infinitos, cadenas que crecen sin control, etc.)."""
    LIMITE_PASOS = 200_000

    def __init__(self, tokens, variables=None):
        super().__init__(tokens, variables)
        self.pasos = 0

    def ejecutar_instruccion(self, instruccion, entorno):
        self.pasos += 1
        if self.pasos > self.LIMITE_PASOS:
            raise RuntimeError(
                f"Se superaron {self.LIMITE_PASOS:,} instrucciones ejecutadas. "
                "¿Hay un ciclo 'mientras' que nunca termina?"
            )
        return super().ejecutar_instruccion(instruccion, entorno)

    def ejecutar(self, operacion, n1, n2):
        resultado = super().ejecutar(operacion, n1, n2)
        if isinstance(resultado, (str, list)) and len(resultado) > LIMITE_TAMANO:
            raise RuntimeError("El resultado es demasiado grande (más de 100.000 elementos).")
        return resultado


def serializar_tokens(tokens):
    return [{"tipo": str(t.token), "valor": str(t.valor)} for t in tokens]


@app.get("/")
def interfaz():
    """Entrega la interfaz gráfica."""
    return FileResponse(BASE / "static" / "index.html")


@app.get("/estado")
def estado():
    return {"lenguaje": "BIP", "estado": "Activo"}


@app.get("/reglas")
def reglas():
    """La interfaz usa estas reglas para colorear el código."""
    with (BASE / "reglas.json").open(encoding="utf-8") as archivo:
        return json.load(archivo)


@app.post("/iniciar")
def ejecutar_codigo(request: CodigoRequest):
    codigo = request.codigo.strip()
    if not codigo:
        return {"exito": False, "etapa": "entrada", "error": "No se ingresó código"}
    if len(codigo) > LIMITE_CODIGO:
        return {"exito": False, "etapa": "entrada",
                "error": f"El programa es muy largo (máximo {LIMITE_CODIGO:,} caracteres)."}

    # 1. Análisis léxico
    try:
        codigo_procesado = convertir_indentacion(codigo.splitlines())
        tokens = analisis(codigo_procesado)
    except ValueError as error:
        return {"exito": False, "etapa": "léxico", "error": str(error), "tokens": []}

    lista_tokens = serializar_tokens(tokens)

    # 2. Análisis sintáctico + ejecución
    buffer_salida = io.StringIO()
    try:
        analizador = SintacticoLimitado(tokens)
        with redirect_stdout(buffer_salida):
            variables_resultado = analizador.analisisPrograma()
    except SyntaxError as error:
        return {"exito": False, "etapa": "sintáctico", "error": str(error),
                "tokens": lista_tokens, "salida_consola": buffer_salida.getvalue() or None}
    except (NameError, TypeError, ValueError, ZeroDivisionError, RuntimeError) as error:
        mensaje = "División entre cero" if isinstance(error, ZeroDivisionError) else str(error)
        return {"exito": False, "etapa": "ejecución", "error": mensaje,
                "tokens": lista_tokens, "salida_consola": buffer_salida.getvalue() or None}
    except Exception as error:
        return {"exito": False, "etapa": "interno", "error": f"Error interno: {error}",
                "tokens": lista_tokens}

    salida = buffer_salida.getvalue()
    if len(salida) > LIMITE_SALIDA:
        salida = salida[:LIMITE_SALIDA] + "\n... (salida recortada)"

    return {
        "exito": True,
        "salida_consola": salida or None,
        "variables_entorno": {k: v for k, v in variables_resultado.items()},
        "funciones": list(analizador.funciones.keys()),
        "tokens": lista_tokens,
        "pasos": analizador.pasos,
    }
