import os
from pathlib import Path

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

PASTA = Path(__file__).parent
ARQUIVO_CSV = PASTA / "avaliacoes.csv"
PASTA_BANCO = PASTA / "chroma_db"

# Modelo que transforma texto em vetor (lista de números que representa o significado).
MODELO_EMBEDDINGS = os.environ.get("MODELO_EMBEDDINGS", "bge-m3")

# num_gpu=0 roda no processador: a GPU AMD R7 240 derruba o Ollama via Vulkan.
embeddings = OllamaEmbeddings(model=MODELO_EMBEDDINGS, num_gpu=0)

# Cada modelo gera vetores diferentes, então cada um tem a sua própria coleção.
banco = Chroma(
    collection_name=f"avaliacoes_{MODELO_EMBEDDINGS}",
    persist_directory=str(PASTA_BANCO),
    embedding_function=embeddings,
)

# Só gera os vetores se a coleção estiver vazia; depois reaproveita o que ficou salvo em disco.
if not banco.get(limit=1)["ids"]:
    df = pd.read_csv(ARQUIVO_CSV)
    documentos = [
        Document(
            page_content=f"{linha.titulo}. {linha.avaliacao}",
            metadata={"nota": int(linha.nota), "data": linha.data},
            id=str(i),
        )
        for i, linha in df.iterrows()
    ]
    banco.add_documents(documents=documentos, ids=[d.id for d in documentos])
    print(f"{len(documentos)} avaliações indexadas no ChromaDB.")

# Quanto menor a distância, mais parecido é o significado. Cada modelo tem a sua escala, então os limites
# (distância máxima, margem em relação à melhor) foram medidos por modelo com as perguntas do avaliar.py.
LIMITES = {
    "mxbai-embed-large": (0.70, 0.10),  # certas: 0.31-0.75 | fora do assunto: a partir de 0.72
    "bge-m3": (0.90, 0.10),  # certas: 0.62-0.86 | erradas: a partir de 0.91 | fora do assunto: 1.36
}
if MODELO_EMBEDDINGS not in LIMITES:
    raise SystemExit(f"Não há limites calibrados para '{MODELO_EMBEDDINGS}'. Adicione o modelo em LIMITES no vetor.py.")
DISTANCIA_MAXIMA, MARGEM_DA_MELHOR = LIMITES[MODELO_EMBEDDINGS]


def buscar(pergunta, k=5):
    resultados = banco.similarity_search_with_score(pergunta, k=k)
    if not resultados:
        return []
    melhor = resultados[0][1]
    return [
        documento
        for documento, distancia in resultados
        if distancia <= DISTANCIA_MAXIMA and distancia <= melhor + MARGEM_DA_MELHOR
    ]
