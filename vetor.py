import hashlib
import os
import re
from pathlib import Path

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

PASTA = Path(__file__).parent
ARQUIVO_CSV = PASTA / "avaliacoes.csv"
PASTA_DOCUMENTOS = PASTA / "documentos"
PASTA_BANCO = PASTA / "chroma_db"
EXTENSOES = {".pdf", ".txt", ".md"}

# Modelo que transforma texto em vetor (lista de números que representa o significado).
MODELO_EMBEDDINGS = os.environ.get("MODELO_EMBEDDINGS", "bge-m3")

# num_gpu=0 roda no processador: a GPU AMD R7 240 derruba o Ollama via Vulkan.
embeddings = OllamaEmbeddings(model=MODELO_EMBEDDINGS, num_gpu=0)

# Documentos longos são quebrados em pedaços de ~500 caracteres. Com 800, um pedaço misturava vários assuntos e a
# busca pôs o trecho certo em 1º lugar em 7 de 10 perguntas; com 500, em 9 de 10. Menor que isso sobra pouco
# contexto para o modelo responder. A sobreposição evita cortar uma ideia no meio.
divisor = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=60)


def carregar_avaliacoes():
    df = pd.read_csv(ARQUIVO_CSV)
    return [
        Document(
            page_content=f"{linha.titulo}. {linha.avaliacao}",
            metadata={"nota": int(linha.nota), "data": linha.data},
        )
        for _, linha in df.iterrows()
    ]


def listar_documentos():
    if not PASTA_DOCUMENTOS.exists():
        return []
    return sorted(p for p in PASTA_DOCUMENTOS.rglob("*") if p.suffix.lower() in EXTENSOES)


def limpar(texto):
    # PDFs com texto justificado costumam vir com espaços duplos ("dólmã  branca"), o que atrapalha a busca.
    return re.sub(r"[ \t]+", " ", texto).strip()


def ler_arquivo(caminho):
    # PDF é lido página por página para cada pedaço saber de que página veio.
    if caminho.suffix.lower() == ".pdf":
        return [(limpar(p.extract_text() or ""), numero) for numero, p in enumerate(PdfReader(caminho).pages, 1)]
    return [(limpar(caminho.read_text(encoding="utf-8")), None)]


def carregar_documentos():
    pedacos = []
    for caminho in listar_documentos():
        for texto, pagina in ler_arquivo(caminho):
            metadata = {"arquivo": caminho.name}
            if pagina:
                metadata["pagina"] = pagina
            pedacos += divisor.create_documents([texto], metadatas=[metadata])
    return pedacos


# Fonte -> (como carregar os textos, quais arquivos ela usa).
FONTES = {
    "avaliacoes": (carregar_avaliacoes, lambda: [ARQUIVO_CSV]),
    "documentos": (carregar_documentos, listar_documentos),
}

# Quanto menor a distância, mais parecido é o significado. Cada modelo tem a sua escala, então os limites
# (distância máxima, margem em relação à melhor) foram medidos por fonte e modelo com as perguntas do avaliar.py.
LIMITES = {
    ("avaliacoes", "mxbai-embed-large"): (0.70, 0.10),  # certas: 0.31-0.75 | fora do assunto: a partir de 0.72
    ("avaliacoes", "bge-m3"): (0.90, 0.10),  # certas: 0.62-0.86 | erradas: a partir de 0.91 | fora: 1.36
    ("documentos", "bge-m3"): (1.10, 0.10),  # certas: 0.55-1.04 | fora do assunto: a partir de 1.37
}


def assinatura(arquivos):
    resumo = hashlib.sha256()
    for arquivo in arquivos:
        resumo.update(arquivo.name.encode())
        resumo.update(arquivo.read_bytes())
    return resumo.hexdigest()


def criar_buscador(fonte):
    if (fonte, MODELO_EMBEDDINGS) not in LIMITES:
        raise SystemExit(
            f"Não há limites calibrados para '{fonte}' com '{MODELO_EMBEDDINGS}'. Adicione em LIMITES no vetor.py."
        )
    distancia_maxima, margem_da_melhor = LIMITES[(fonte, MODELO_EMBEDDINGS)]
    carregar, listar_arquivos = FONTES[fonte]

    # Cada fonte e cada modelo geram vetores diferentes, então cada combinação tem a sua coleção.
    colecao = f"{fonte}_{MODELO_EMBEDDINGS}"
    banco = Chroma(collection_name=colecao, persist_directory=str(PASTA_BANCO), embedding_function=embeddings)

    # A assinatura é um resumo do conteúdo dos arquivos. Se mudou (arquivo novo, editado ou apagado), reindexa.
    arquivo_assinatura = PASTA_BANCO / f"{colecao}.assinatura"
    atual = assinatura(listar_arquivos())
    if not arquivo_assinatura.exists() or arquivo_assinatura.read_text() != atual:
        banco.reset_collection()
        textos = carregar()
        if textos:
            banco.add_documents(textos)
        arquivo_assinatura.write_text(atual)
        print(f"{len(textos)} textos de '{fonte}' indexados no ChromaDB.")

    def buscar(pergunta, k=5):
        resultados = banco.similarity_search_with_score(pergunta, k=k)
        if not resultados:
            return []
        melhor = resultados[0][1]
        return [
            documento
            for documento, distancia in resultados
            if distancia <= distancia_maxima and distancia <= melhor + margem_da_melhor
        ]

    return buscar
