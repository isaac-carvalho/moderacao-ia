from graph.state import AgentState


def rota_pos_analise(state: AgentState) -> str:
    """Aresta condicional: se problematico, pesquisa politicas. Senao, aprova."""
    if state["status_da_moderacao"] == "Problematico":
        return "pesquisar_politicas"
    return "fim_aprovado"
