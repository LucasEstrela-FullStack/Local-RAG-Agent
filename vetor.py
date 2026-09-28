from pathlib import Path

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

PASTA = Path(__file__).parent
ARQUIVO_CSV = PASTA / "avaliacoes.csv"
PASTA_BANCO = PASTA / "chroma_db"

# Modelo que transforma texto em vetor (lista de números que representa o significado).
# num_gpu=0 roda no processador: a GPU AMD R7 240 derruba o Ollama via Vulkan.
embeddings = OllamaEmbeddings(model="mxbai-embed-large", num_gpu=0)

banco = Chroma(
    collection_name="avaliacoes_pizzaria",
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

# Quanto menor a distância, mais parecido é o significado. Valores medidos com as perguntas de teste:
# as avaliações certas ficaram entre 0.38 e 0.63, e uma pergunta fora do assunto começou em 0.72.
DISTANCIA_MAXIMA = 0.70
MARGEM_DA_MELHOR = 0.10


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
