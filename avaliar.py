from vetor import buscar

# Pergunta -> títulos das avaliações que a busca deveria trazer. Lista vazia = pergunta fora do assunto.
CASOS = {
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
}


def titulo(documento):
    return documento.page_content.split(".")[0]


acertos = primeiro_certo = total_trazidas = total_ruido = 0

for pergunta, esperadas in CASOS.items():
    trazidas = [titulo(d) for d in buscar(pergunta)]
    faltando = [t for t in esperadas if t not in trazidas]
    ruido = [t for t in trazidas if t not in esperadas]

    acertou = not faltando if esperadas else not trazidas
    acertos += acertou
    primeiro_certo += bool(esperadas) and bool(trazidas) and trazidas[0] in esperadas
    total_trazidas += len(trazidas)
    total_ruido += len(ruido)

    print(f"{'✅' if acertou else '❌'} {pergunta}")
    if faltando:
        print(f"     faltou: {', '.join(faltando)}")
    if ruido:
        print(f"     ruído:  {', '.join(ruido)}")

n = len(CASOS)
n_no_assunto = sum(1 for e in CASOS.values() if e)
print("\n📊 Resultado")
print(f"   Acertos:                  {acertos}/{n} ({acertos / n:.0%})")
print(f"   Certa em 1º lugar:        {primeiro_certo}/{n_no_assunto} ({primeiro_certo / n_no_assunto:.0%})")
print(f"   Avaliações por pergunta:  {total_trazidas / n:.1f}")
print(f"   Avaliações irrelevantes:  {total_ruido} de {total_trazidas}")
