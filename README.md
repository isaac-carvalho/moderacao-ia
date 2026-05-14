# Sistema de Moderacao de Conteudo Assistido por IA

Sistema multi-agentes com **LangGraph** para moderacao de comentarios em plataforma de cursos online. Implementa **Human in the Loop (HITL)** para garantir que um moderador humano tenha a decisao final.

## Arquitetura

```
[Comentario] -> Analisador -> (condicional) -> Pesquisador de Politicas -> Revisor
                    |                                                         |
                    v (se ok)                                                 v
               APROVADO (fim)                                    [INTERRUPT - HITL]
                                                                      |
                                                          sim / nao / editar
                                                                      |
                                                                      v
                                                             Executar Acao Final
```

### Agentes

| Agente | Responsabilidade |
|---|---|
| **Analisador** | Classifica o comentario como POSITIVO, NEUTRO ou PROBLEMATICO |
| **Pesquisador de Politicas** | Busca diretrizes internas + contexto externo (Tavily) |
| **Revisor** | Consolida analise + politicas e recomenda acao (APROVAR/REMOVER/EDITAR) |
| **Executar Acao Final** | Registra a decisao final (apos aprovacao humana) |

### Human in the Loop

O sistema **pausa antes da acao final** e apresenta a recomendacao ao moderador:

- **sim** — confirma a acao sugerida pelo agente
- **nao** — cancela a acao
- **editar** — moderador reescreve a justificativa e altera o status (Etapa 3: `update_state`)

## Como configurar

```bash
git clone https://github.com/recuperarcontato4-prog/moderacao-ia.git
cd moderacao-ia
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

cp .env.example .env
chmod 600 .env
# Edite .env com suas chaves
```

Chaves necessarias:
- **OpenAI:** https://platform.openai.com/api-keys
- **Tavily:** https://app.tavily.com/home (gratis, 1000 buscas/mes)

## Como executar

```bash
python main.py
```

O sistema apresenta 5 comentarios de exemplo ou aceita input livre.

## Exemplos de interacao

### Comentario positivo (aprovacao automatica)
```
Comentario: "Excelente aula, professor! Aprendi muito."
[AGENTE: analisador]
  CLASSIFICACAO: POSITIVO
  -> Aprovado automaticamente (sem interrupcao)
```

### Comentario spam (HITL ativado)
```
Comentario: "Compre seguidores em meusite.com"
[AGENTE: analisador]     -> PROBLEMATICO (spam)
[AGENTE: pesquisador]    -> Politica 2: Proibido spam e links externos
[AGENTE: revisor]        -> ACAO: REMOVER

PAUSA PARA REVISAO HUMANA
Escolha: [sim] confirmar | [nao] cancelar | [editar] modificar
> editar
Nova justificativa: "Removido por conter link externo nao autorizado, conforme politica 2"
Novo status: Removido
```

### Comentario ambiguo (valor do HITL)
```
Comentario: "Esse conteudo e meio fraco comparado ao outro curso"
[AGENTE: revisor] -> ACAO: EDITAR (linguagem inadequada)

PAUSA — moderador decide APROVAR com justificativa:
"Critica valida e respeitosa. Aprovado conforme politica 5."
```

## Tecnologias

- **Python 3.12**
- **LangGraph** — Orquestracao de agentes com grafo de estado
- **OpenAI GPT-3.5-turbo** — Modelo de linguagem para analise
- **Tavily Search** — Busca contextual de politicas
- **SQLite** — Persistencia de checkpoints para pausar/retomar
- **Human in the Loop** — `interrupt_before` + `update_state`

## Conceitos aplicados

| Conceito | Implementacao |
|---|---|
| Multi-agentes | 4 nos especializados no StateGraph |
| Estado compartilhado | `AgentState` (TypedDict) com 6 campos |
| Aresta condicional | `rota_pos_analise` direciona fluxo |
| HITL (aprovacao) | `interrupt_before=["executar_acao_final"]` |
| HITL (edicao) | `graph.aupdate_state()` modifica estado em runtime |
| Persistencia | `AsyncSqliteSaver` para checkpoints |
| reduce_messages | Substitui mensagens por ID em vez de anexar |

## Estrutura

```
moderacao-ia/
├── main.py                 # Ponto de entrada + logica HITL
├── graph/
│   ├── state.py            # AgentState + reduce_messages
│   ├── nodes.py            # 4 agentes (nos do grafo)
│   ├── edges.py            # Aresta condicional
│   └── builder.py          # Construcao e compilacao do grafo
├── policies/
│   └── diretrizes.txt      # Politicas da comunidade
├── utils/
│   └── llm.py              # Configuracao do LLM
├── .env.example
├── requirements.txt
└── README.md
```

## Licenca

MIT
