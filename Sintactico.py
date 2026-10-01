class Retorno(Exception):
    def __init__(self, valor):
        self.valor = valor


class Funcion:
    def __init__(self, parametros, cuerpo):
        self.parametros = parametros
        self.cuerpo = cuerpo


class Sintactico:
    def __init__(self, tokens, variables=None):
        self.tokens = tokens
        self.pos = 0
        self.variables = variables if variables is not None else {}
        self.funciones = {}
        self.clases = {}

    def actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def es(self, tipo):
        return self.actual() is not None and self.actual().token == tipo

    def consumir(self, tipo):
        token = self.actual()
        if token is None or token.token != tipo:
            encontrado = 'fin del programa' if token is None else f'{token.token} ({token.valor})'
            raise SyntaxError(f'Se esperaba {tipo}, llegó {encontrado}.')
        self.pos += 1
        return token

    def aceptar(self, tipo):
        return self.consumir(tipo) if self.es(tipo) else None

    def analisisPrograma(self):
        programa = self.analizar_bloque()
        self.ejecutar_bloque(programa, self.variables)
        return self.variables

    def analizar_bloque(self, cerrado=False):
        instrucciones = []
        while self.actual() is not None and not self.es('LLAVE_DERECHA'):
            instrucciones.append(self.analizar_instruccion())
        if cerrado:
            self.consumir('LLAVE_DERECHA')
        return instrucciones

    def analizar_bloque_llaves(self):
        self.consumir('LLAVE_IZQUIERDA')
        return self.analizar_bloque(cerrado=True)

    def analizar_instruccion(self):
        token = self.actual()
        if token is None:
            raise SyntaxError('Falta una instrucción.')
        if token.token == 'IDENTIFICADOR':
            nombre = self.consumir('IDENTIFICADOR').valor
            if self.aceptar('ASIGNACION'):
                expresion = self.analizar_expresion()
                self.aceptar('PUNTO_Y_COMA')
                return ('asignacion', nombre, expresion)
            llamada = self.analizar_llamada(nombre)
            self.aceptar('PUNTO_Y_COMA')
            return ('expresion', llamada)
        if token.token == 'Palabra reservada print':
            self.consumir(token.token)
            self.consumir('PARENTESIS_IZQUIERDO')
            expresion = self.analizar_expresion()
            self.consumir('PARENTESIS_DERECHO')
            self.aceptar('PUNTO_Y_COMA')
            return ('imprimir', expresion)
        if token.token == 'Condicional if':
            self.consumir(token.token)
            condicion = self.analizar_condicion()
            cuerpo = self.analizar_bloque_llaves()
            sino = self.analizar_bloque_llaves() if self.aceptar('Condicional else') else []
            return ('si', condicion, cuerpo, sino)
        if token.token == 'Condicional while':
            self.consumir(token.token)
            return ('mientras', self.analizar_condicion(), self.analizar_bloque_llaves())
        if token.token == 'Palabra reservada for':
            self.consumir(token.token)
            variable = self.consumir('IDENTIFICADOR').valor
            self.consumir('Palabra reservada in')
            return ('para', variable, self.analizar_expresion(), self.analizar_bloque_llaves())
        if token.token == 'Palabra reservada return':
            self.consumir(token.token)
            expresion = None if self.es('PUNTO_Y_COMA') or self.es('LLAVE_DERECHA') else self.analizar_expresion()
            self.aceptar('PUNTO_Y_COMA')
            return ('retornar', expresion)
        if token.token == 'Palabra reservada def':
            self.consumir(token.token)
            nombre = self.consumir('IDENTIFICADOR').valor
            self.consumir('PARENTESIS_IZQUIERDO')
            parametros = []
            if not self.es('PARENTESIS_DERECHO'):
                parametros.append(self.consumir('IDENTIFICADOR').valor)
                while self.aceptar('COMA'):
                    parametros.append(self.consumir('IDENTIFICADOR').valor)
            self.consumir('PARENTESIS_DERECHO')
            return ('metodo', nombre, parametros, self.analizar_bloque_llaves())
        if token.token == 'Palabra reservada class':
            self.consumir(token.token)
            nombre = self.consumir('IDENTIFICADOR').valor
            return ('clase', nombre, self.analizar_bloque_llaves())
        if token.token == 'Palabra reservada import':
            self.consumir(token.token)
            modulo = self.consumir('IDENTIFICADOR').valor
            self.aceptar('PUNTO_Y_COMA')
            return ('importar', modulo)
        raise SyntaxError(f'Instrucción inesperada: {token.valor}')

    def analizar_condicion(self):
        self.consumir('PARENTESIS_IZQUIERDO')
        condicion = self.analizar_expresion()
        self.consumir('PARENTESIS_DERECHO')
        return condicion

    def analizar_expresion(self):
        izquierda = self.analizar_suma()
        comparadores = {'IGUAL_IGUAL', 'DIFERENTE', 'MAYOR', 'MENOR', 'MAYOR_IGUAL', 'MENOR_IGUAL'}
        while self.actual() is not None and self.actual().token in comparadores:
            operador = self.consumir(self.actual().token).token
            izquierda = ('binaria', operador, izquierda, self.analizar_suma())
        return izquierda

    def analizar_suma(self):
        izquierda = self.analizar_producto()
        while self.actual() is not None and self.actual().token in ('SUMA', 'RESTA'):
            operador = self.consumir(self.actual().token).token
            izquierda = ('binaria', operador, izquierda, self.analizar_producto())
        return izquierda

    def analizar_producto(self):
        izquierda = self.analizar_unaria()
        while self.actual() is not None and self.actual().token in ('MULTIPLICACION', 'DIVISION', 'MODULO'):
            operador = self.consumir(self.actual().token).token
            izquierda = ('binaria', operador, izquierda, self.analizar_unaria())
        return izquierda

    def analizar_unaria(self):
        if self.aceptar('RESTA'):
            return ('negacion', self.analizar_unaria())
        return self.analizar_primaria()

    def analizar_primaria(self):
        token = self.actual()
        if token is None:
            raise SyntaxError('Falta un valor en la expresión.')
        if token.token in ('NUMERO', 'NUMERO_DECIMAL'):
            self.consumir(token.token)
            return ('valor', float(token.valor))
        if token.token == 'Cadena tipo String':
            self.consumir(token.token)
            return ('valor', token.valor[1:-1])
        if token.token == 'IDENTIFICADOR':
            nombre = self.consumir('IDENTIFICADOR').valor
            return self.analizar_llamada(nombre) if self.es('PARENTESIS_IZQUIERDO') else ('variable', nombre)
        if self.aceptar('PARENTESIS_IZQUIERDO'):
            expresion = self.analizar_expresion()
            self.consumir('PARENTESIS_DERECHO')
            return expresion
        if self.aceptar('CIZQ'):
            valores = []
            if not self.es('CDER'):
                valores.append(self.analizar_expresion())
                while self.aceptar('COMA'):
                    valores.append(self.analizar_expresion())
            self.consumir('CDER')
            return ('lista', valores)
        raise SyntaxError(f'Valor inesperado: {token.valor}')

    def analizar_llamada(self, nombre):
        self.consumir('PARENTESIS_IZQUIERDO')
        argumentos = []
        if not self.es('PARENTESIS_DERECHO'):
            argumentos.append(self.analizar_expresion())
            while self.aceptar('COMA'):
                argumentos.append(self.analizar_expresion())
        self.consumir('PARENTESIS_DERECHO')
        return ('llamada', nombre, argumentos)

    def ejecutar_bloque(self, instrucciones, entorno):
        for instruccion in instrucciones:
            self.ejecutar_instruccion(instruccion, entorno)

    def ejecutar_instruccion(self, instruccion, entorno):
        tipo = instruccion[0]
        if tipo == 'asignacion':
            entorno[instruccion[1]] = self.evaluar(instruccion[2], entorno)
        elif tipo == 'imprimir':
            print(self.evaluar(instruccion[1], entorno))
        elif tipo == 'expresion':
            self.evaluar(instruccion[1], entorno)
        elif tipo == 'si':
            cuerpo = instruccion[2] if self.evaluar(instruccion[1], entorno) else instruccion[3]
            self.ejecutar_bloque(cuerpo, entorno)
        elif tipo == 'mientras':
            while self.evaluar(instruccion[1], entorno):
                self.ejecutar_bloque(instruccion[2], entorno)
        elif tipo == 'para':
            for valor in self.evaluar(instruccion[2], entorno):
                entorno[instruccion[1]] = valor
                self.ejecutar_bloque(instruccion[3], entorno)
        elif tipo == 'retornar':
            raise Retorno(None if instruccion[1] is None else self.evaluar(instruccion[1], entorno))
        elif tipo == 'metodo':
            self.funciones[instruccion[1]] = Funcion(instruccion[2], instruccion[3])
        elif tipo == 'clase':
            self.clases[instruccion[1]] = instruccion[2]

    def evaluar(self, expresion, entorno):
        tipo = expresion[0]
        if tipo == 'valor':
            return expresion[1]
        if tipo == 'variable':
            return self.resolverVariable(expresion[1], entorno)
        if tipo == 'lista':
            return [self.evaluar(valor, entorno) for valor in expresion[1]]
        if tipo == 'negacion':
            return -self.evaluar(expresion[1], entorno)
        if tipo == 'binaria':
            izquierda = self.evaluar(expresion[2], entorno)
            derecha = self.evaluar(expresion[3], entorno)
            return self.ejecutar(expresion[1], izquierda, derecha)
        if tipo == 'llamada':
            return self.ejecutar_llamada(expresion[1], expresion[2], entorno)
        raise SyntaxError('Expresión desconocida.')

    def ejecutar_llamada(self, nombre, argumentos, entorno):
        if nombre == 'range':
            valores = [self.evaluar(argumento, entorno) for argumento in argumentos]
            if len(valores) not in (1, 2, 3):
                raise TypeError('range esperaba entre 1 y 3 argumentos.')
            return list(range(*(int(valor) for valor in valores)))
        if nombre not in self.funciones:
            raise NameError(f'El método {nombre!r} no existe.')
        funcion = self.funciones[nombre]
        if len(argumentos) != len(funcion.parametros):
            raise TypeError(f'El método {nombre!r} esperaba {len(funcion.parametros)} argumentos.')
        local = dict(entorno)
        valores = [self.evaluar(argumento, entorno) for argumento in argumentos]
        local.update(zip(funcion.parametros, valores))
        try:
            self.ejecutar_bloque(funcion.cuerpo, local)
        except Retorno as retorno:
            return retorno.valor
        return None

    def resolverVariable(self, nombre, entorno=None):
        entorno = self.variables if entorno is None else entorno
        if nombre not in entorno:
            raise NameError(f'La variable {nombre!r} no tiene un valor asignado.')
        return entorno[nombre]

    def ejecutar(self, operacion, n1, n2):
        def sumar():
            if isinstance(n1, str) or isinstance(n2, str):
                return str(n1) + str(n2)
            return n1 + n2

        operaciones = {
            'SUMA': sumar,
            'RESTA': lambda: n1 - n2,
            'MULTIPLICACION': lambda: n1 * n2,
            'DIVISION': lambda: n1 / n2,
            'MODULO': lambda: n1 % n2,
            'IGUAL_IGUAL': lambda: n1 == n2,
            'DIFERENTE': lambda: n1 != n2,
            'MAYOR': lambda: n1 > n2,
            'MENOR': lambda: n1 < n2,
            'MAYOR_IGUAL': lambda: n1 >= n2,
            'MENOR_IGUAL': lambda: n1 <= n2,
        }
        if operacion not in operaciones:
            raise SyntaxError(f'Operador desconocido: {operacion}')
        return operaciones[operacion]()
