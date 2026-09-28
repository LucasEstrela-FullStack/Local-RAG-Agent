from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from vetor import buscador

modelo = OllamaLLM(model="llama3.2", num_gpu=0)

template = """
Você é um especialista em responder perguntas sobre uma pizzaria.
Responda em português, usando apenas as avaliações abaixo. Se elas não trouxerem a resposta, diga que não sabe.

Avaliações relevantes:
{avaliacoes}

Pergunta: {pergunta}
"""
prompt = ChatPromptTemplate.from_template(template)
cadeia = prompt | modelo


def formatar(documentos):
    return "\n".join(
        f"- (nota {d.metadata['nota']}, {d.metadata['data']}) {d.page_content}"
        for d in documentos
    )


while True:
    print("\n-------------------------------")
    pergunta = input("Faça sua pergunta (q para sair): ").strip()
    if pergunta.lower() == "q":
        break
    if not pergunta:
        continue

    documentos = buscador.invoke(pergunta)
    resposta = cadeia.invoke({"avaliacoes": formatar(documentos), "pergunta": pergunta})
    print(f"\n{resposta}")
