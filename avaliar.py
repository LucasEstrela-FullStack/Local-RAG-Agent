import sys

from vetor import criar_buscador

# Pergunta -> trechos de texto que a busca deveria trazer. Lista vazia = pergunta fora do assunto.
CASOS = {
    "avaliacoes": {
        "Como é a entrega?": ["Entrega muito atrasada", "Pedido errado no delivery"],
        "Posso levar meu cachorro?": ["Aceita pet"],
        "Tem algo para celíaco?": ["Opção sem glúten decente"],
        "O lugar é bom para cadeirante?": ["Acessibilidade"],
        "Qual a melhor sobremesa?": ["Sobremesa imperdível"],
        "Tem música ao vivo?": ["Música ao vivo"],
        "Tem opção vegana?": ["Opções veganas surpreendentes"],
        "É um bom lugar para levar crianças?": ["Ótimo para família"],
        "É fácil estacionar?": ["Estacionamento ruim"],
        "Até que horas funciona?": ["Horário de funcionamento"],
        "Que cerveja combina com pizza?": ["Cerveja artesanal ótima"],
        "Os garçons são educados?": ["Atendimento grosseiro"],
        "Tem rodízio?": ["Rodízio vale a pena"],
        "Qual a capital da França?": [],
        "Quem ganhou a Copa de 2002?": [],
    },
    "documentos": {
        "Quanto custa o rodízio?": ["R$ 69,90"],
        "Qual a taxa de entrega?": ["R$ 5,00 para endereços"],
        "Qual o pedido mínimo para delivery?": ["pedido mínimo para delivery"],
        "O que acontece se a entrega atrasar?": ["cupom de 20%"],
        "Quais as formas de pagamento na entrega?": ["Aceitamos Pix"],
        "Quanto custa a borda recheada?": ["Borda recheada"],
        "Qual a temperatura do forno?": ["450 °C"],
        "Como evitar contaminação com glúten na cozinha?": ["utensílios roxos"],
        "Qual é o uniforme da cozinha?": ["dólmã branca"],
        "Quantos atrasos geram advertência?": ["Três atrasos"],
        "Qual a capital da França?": [],
        "Quem ganhou a Copa de 2002?": [],
    },
}


def rotulo(documento):
    if "arquivo" in documento.metadata:
        pagina = f" p.{documento.metadata['pagina']}" if "pagina" in documento.metadata else ""
        return f"{documento.metadata['arquivo']}{pagina}: {documento.page_content[:40]!r}"
    return documento.page_content.split(".")[0]


fonte = sys.argv[1] if len(sys.argv) > 1 else "avaliacoes"
buscar = criar_buscador(fonte)
casos = CASOS[fonte]
acertos = primeiro_certo = total_trazidos = total_ruido = 0

for pergunta, esperados in casos.items():
    trazidos = buscar(pergunta)
    faltando = [e for e in esperados if not any(e in d.page_content for d in trazidos)]
    ruido = [d for d in trazidos if not any(e in d.page_content for e in esperados)]

    acertou = not faltando if esperados else not trazidos
    acertos += acertou
    primeiro_certo += bool(esperados) and bool(trazidos) and any(e in trazidos[0].page_content for e in esperados)
    total_trazidos += len(trazidos)
    total_ruido += len(ruido)

    print(f"{'✅' if acertou else '❌'} {pergunta}")
    if faltando:
        print(f"     faltou: {', '.join(faltando)}")
    for d in ruido:
        print(f"     ruído:  {rotulo(d)}")

n = len(casos)
n_no_assunto = sum(1 for e in casos.values() if e)
print(f"\n📊 Resultado ({fonte})")
print(f"   Acertos:                  {acertos}/{n} ({acertos / n:.0%})")
print(f"   Certo em 1º lugar:        {primeiro_certo}/{n_no_assunto} ({primeiro_certo / n_no_assunto:.0%})")
print(f"   Textos por pergunta:      {total_trazidos / n:.1f}")
print(f"   Textos irrelevantes:      {total_ruido} de {total_trazidos}")
