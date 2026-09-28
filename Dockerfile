FROM python:3.14-slim

WORKDIR /app

# uv instala os pacotes bem mais rápido que o pip. Ele é montado só durante este passo e não fica na imagem.
COPY requirements.txt .
RUN --mount=from=ghcr.io/astral-sh/uv:latest,source=/uv,target=/bin/uv \
    uv pip install --system --no-cache -r requirements.txt

COPY avaliacoes.csv vetor.py main.py avaliar.py ./
# Só os exemplos entram na imagem; seus documentos entram montando a pasta com -v ./documentos:/app/documentos
COPY documentos/exemplo-* documentos/

RUN useradd --create-home agente && mkdir chroma_db && chown agente chroma_db
USER agente

# Por padrão usa o Ollama instalado na máquina; o docker-compose.yml troca para o container do Ollama.
ENV PYTHONUNBUFFERED=1 \
    OLLAMA_HOST=http://host.docker.internal:11434

CMD ["python", "main.py"]
