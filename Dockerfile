FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY AnalisisLexico.py Sintactico.py Token.py mainCompiler.py servidor.py reglas.json ./
COPY static ./static

# Los servicios de hosting (Render, Railway, etc.) indican el puerto en la variable PORT.
# En tu computador, si no existe, se usa el 8000.
ENV PORT=8000
EXPOSE 8000
CMD uvicorn servidor:app --host 0.0.0.0 --port ${PORT}
