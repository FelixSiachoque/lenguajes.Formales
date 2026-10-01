class Token:
    def __init__(self, valor, token):
        self.token = token
        self.valor = valor

    def __repr__(self):
        return f"Token({self.token}, {self.valor!r})"
