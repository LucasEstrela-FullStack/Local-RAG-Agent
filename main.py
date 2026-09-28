import sys

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from ollama import ResponseError

# temperature=0 deixa as respostas estáveis: a mesma pergunta com as mesmas avaliações dá a mesma resposta.
modelo = OllamaLLM(model="llama3.2", num_gpu=0, temperature=0)

template = """
Você é um especialista em responder perguntas sobre uma pizzaria.
Responda em português, de forma curta, usando apenas as avaliações de clientes abaixo.
Se nenhuma avaliação tratar do assunto da pergunta, responda exatamente: "Não encontrei nada sobre isso nas avaliações."

Avaliações de clientes:
{avaliacoes}

Pergunta: {pergunta}
"""
cadeia = ChatPromptTemplate.from_template(template) | modelo


def formatar(documentos):
    if not documentos:
        return "(nenhuma avaliação fala sobre isso)"
    return "\n".join(
        f"- (nota {d.metadata['nota']}, {d.metadata['data']}) {d.page_content}"
        for d in documentos
    )


def conversar():
    # Importado aqui porque, na primeira execução, o vetor.py já chama o Ollama para indexar as avaliações.
    from vetor import buscar

    # A memória da conversa é o assunto atual: as perguntas que levaram às últimas avaliações encontradas.
    assunto = ""

    while True:
        print("\n-------------------------------")
        pergunta = input("Faça sua pergunta (q para sair): ").strip()
        if pergunta.lower() == "q":
            break
        if not pergunta:
            continue

        # Se a pergunta sozinha acha avaliações, é um assunto novo. Se não acha, pode ser um acompanhamento
        # ("E ela é cara?"): junta com o assunto anterior, tanto na busca quanto no que o modelo lê,
        # para que o "ela" faça sentido ("Tem opção vegana? E ela é cara?").
        documentos = buscar(pergunta)
        if documentos:
            assunto = pergunta
        elif assunto:
            documentos = buscar(f"{assunto} {pergunta}")
            if documentos:
                assunto = f"{assunto} {pergunta}"
                pergunta = assunto
                print(f"(entendi como: {pergunta})")

        print()
        # stream devolve a resposta em pedaços conforme o modelo gera, em vez de esperar o texto inteiro.
        for pedaco in cadeia.stream({"avaliacoes": formatar(documentos), "pergunta": pergunta}):
            print(pedaco, end="", flush=True)
        print()


if __name__ == "__main__":
    try:
        conversar()
    except ConnectionError:
        sys.exit(
            "\n❌ Não consegui falar com o Ollama. Abra o app do Ollama (ou rode `ollama serve`) e tente de novo."
            "\n   No Docker, confira se a variável OLLAMA_HOST aponta para o Ollama certo."
        )
    except ResponseError as erro:
        if erro.status_code != 404:
            raise
        sys.exit(f"\n❌ Modelo não encontrado ({erro.error}).\n   Baixe com: ollama pull llama3.2 && ollama pull bge-m3")
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Até mais!")
