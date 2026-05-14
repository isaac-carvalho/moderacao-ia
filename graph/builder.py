from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.nodes import (
    agente_analisador,
    agente_pesquisador_politicas,
    agente_revisor,
    executar_acao_final,
)
from graph.edges import rota_pos_analise


def build_graph(checkpointer=None):
    """Constroi e compila o grafo de moderacao."""
    workflow = StateGraph(AgentState)

    # Adiciona nos (agentes)
    workflow.add_node("analisador", agente_analisador)
    workflow.add_node("pesquisar_politicas", agente_pesquisador_politicas)
    workflow.add_node("revisor", agente_revisor)
    workflow.add_node("executar_acao_final", executar_acao_final)

    # Ponto de entrada
    workflow.set_entry_point("analisador")

    # Aresta condicional: problematico -> pesquisa | ok -> fim
    workflow.add_conditional_edges(
        "analisador",
        rota_pos_analise,
        {
            "pesquisar_politicas": "pesquisar_politicas",
            "fim_aprovado": END,
        },
    )

    # Fluxo linear apos pesquisa
    workflow.add_edge("pesquisar_politicas", "revisor")
    workflow.add_edge("revisor", "executar_acao_final")
    workflow.add_edge("executar_acao_final", END)

    # Compila com checkpoint + interrupt antes da acao final (HITL)
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["executar_acao_final"],
    )
