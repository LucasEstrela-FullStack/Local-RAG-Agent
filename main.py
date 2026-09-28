from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from vetor import buscar

modelo = OllamaLLM(model="llama3.2", num_gpu=0)

template = """
Você é um especialista em responder perguntas sobre uma pizzaria.
Responda em português, usando apenas as avaliações de clientes abaixo.
Se nenhuma avaliação tratar do assunto da pergunta, responda exatamente: "Não encontrei nada sobre isso nas avaliações."

Avaliações de clientes:
{avaliacoes}

Pergunta: {pergunta}
"""
prompt = ChatPromptTemplate.from_template(template)
cadeia = prompt | modelo


def formatar(documentos):
    if not documentos:
        return "(nenhuma avaliação fala sobre isso)"
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

    documentos = buscar(pergunta)
    print()
    # stream devolve a resposta em pedaços conforme o modelo gera, em vez de esperar o texto inteiro.
    for pedaco in cadeia.stream({"avaliacoes": formatar(documentos), "pergunta": pergunta}):
        print(pedaco, end="", flush=True)
    print()
