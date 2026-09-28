# 🍕 Local RAG Agent

Um agente que responde perguntas sobre uma pizzaria lendo as avaliações dos clientes. Montei para aprender na prática como funciona RAG, e tudo roda no meu computador: sem API paga, sem chave e sem mandar nada para a nuvem. 🔒

```text
Faça sua pergunta (q para sair): Tem opção para quem não pode comer glúten?

Sim, existe opção sem glúten decente. Eles têm massa sem glúten feita em área
separada, embora a textura não seja igual à tradicional.
```

## 🧠 Como funciona

O modelo não sabe nada sobre a pizzaria. Então, antes de responder, o agente procura as avaliações que mais têm a ver com a pergunta e entrega elas junto com o prompt.

1. 📄 Cada avaliação do `avaliacoes.csv` vira um vetor com o `mxbai-embed-large` e fica salva no ChromaDB.
2. 🔎 A pergunta também vira vetor, e o ChromaDB devolve até 5 avaliações parecidas. As que estão longe demais do assunto são descartadas, e se nada sobrar o agente diz que não encontrou nada.
3. ✍️ O `llama3.2` lê essas avaliações e escreve a resposta.

Stack: 🐍 Python, 🦙 Ollama, 🔗 LangChain, 🗄️ ChromaDB e 🐼 pandas.

## 🚀 Rodando

Você precisa do [Ollama](https://ollama.com/download) instalado e de uns 3 GB livres para os modelos.

```bash
ollama pull llama3.2
ollama pull mxbai-embed-large

git clone https://github.com/LucasEstrela-FullStack/Local-RAG-Agent.git
cd Local-RAG-Agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # no Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python main.py
```

Na primeira vez ele indexa as 25 avaliações; depois reaproveita o banco salvo em `chroma_db/`. Digite `q` para sair. 👋

Algumas perguntas para testar: *"Posso levar meu cachorro?"*, *"Qual a melhor sobremesa?"*, *"Quais são as principais reclamações?"*

## 📁 Arquivos

| Arquivo | O que faz |
|---|---|
| `avaliacoes.csv` | As 25 avaliações (título, data, nota e texto) |
| `vetor.py` | Gera os vetores, salva no ChromaDB e busca as avaliações relevantes |
| `main.py` | Recebe a pergunta, busca as avaliações e gera a resposta |
| `avaliar.py` | Mede quanto a busca acerta com 15 perguntas de teste |

## 📊 Medindo a busca

```bash
python avaliar.py
```

O script faz 15 perguntas com resposta conhecida (duas delas fora do assunto, que não devem trazer nada) e mostra o que faltou e o que veio de ruído. Uso ele para comparar ajustes e modelos com números, e não no olho. Resultado atual com o `mxbai-embed-large`:

| Métrica | Resultado |
|---|---|
| ✅ Acertos | 13/15 (87%) |
| 🥇 Avaliação certa em 1º lugar | 10/13 (77%) |
| 🗑️ Avaliações irrelevantes | 14 de 26 trazidas |

## 💡 Coisas que aprendi no caminho

- 🖥️ **GPU antiga trava o Ollama.** A minha (AMD R7 240) derrubava o processo, então deixei os modelos no processador com `num_gpu=0`. Se a sua placa funciona, tire isso de `vetor.py` e `main.py` que fica bem mais rápido.
- ⏳ **A demora é o modelo lendo, não escrevendo.** Na CPU, o `llama3.2` passa uns 7 segundos lendo o prompt (as 5 avaliações + a pergunta) antes da primeira palavra. Por isso a busca descarta as avaliações irrelevantes: prompt menor, leitura mais rápida. Depois disso a resposta vai aparecendo na tela aos poucos, graças ao `cadeia.stream()`. A primeira pergunta demora mais, porque o modelo ainda está sendo carregado na memória.
- 🎯 **Modelo pequeno leva o prompt ao pé da letra.** Com "se não souber, diga que não sabe", o `llama3.2` respondia "Não sabe" mesmo recebendo a avaliação certa. Trocar por uma frase exata ("Não encontrei nada sobre isso nas avaliações.") resolveu.
- 🔁 **Mudou o CSV ou o modelo de embeddings?** Apague a pasta `chroma_db/` para ele indexar de novo.
- 🌎 **A busca em português ainda erra.** O `mxbai-embed-large` foi feito para inglês e às vezes traz a avaliação errada em primeiro lugar.

## 🗺️ Próximos passos

- [x] ⚡ Mostrar a resposta enquanto ela é gerada
- [ ] 🌎 Testar um modelo de embeddings multilíngue, como o `bge-m3`
- [x] 📊 Criar um script para medir quanto a busca acerta
- [ ] 💬 Lembrar da conversa para perguntas de acompanhamento
