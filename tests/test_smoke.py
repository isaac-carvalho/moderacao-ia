"""Smoke test — verifica state, edges e builder sem chamar LLM."""
import pytest

from graph.state import AgentState, reduce_messages
from graph.edges import rota_pos_analise


def test_agent_state_fields():
    """AgentState aceita todos os campos esperados."""
    state: AgentState = {
        "comentario_original": "teste",
        "politicas_relevantes": "",
        "analise_do_agente": "",
        "status_da_moderacao": "Aprovado",
        "justificativa_final": "",
        "messages": [],
    }
    assert state["status_da_moderacao"] == "Aprovado"


def test_rota_aprovado():
    state: AgentState = {
        "comentario_original": "bom comentario",
        "politicas_relevantes": "",
        "analise_do_agente": "",
        "status_da_moderacao": "Aprovado",
        "justificativa_final": "",
        "messages": [],
    }
    assert rota_pos_analise(state) == "fim_aprovado"


def test_rota_problematico():
    state: AgentState = {
        "comentario_original": "comentario ruim",
        "politicas_relevantes": "",
        "analise_do_agente": "",
        "status_da_moderacao": "Problematico",
        "justificativa_final": "",
        "messages": [],
    }
    assert rota_pos_analise(state) == "pesquisar_politicas"


def test_reduce_messages_append():
    from langchain_core.messages import AIMessage
    left = [AIMessage(content="a", id="1")]
    right = [AIMessage(content="b", id="2")]
    merged = reduce_messages(left, right)
    assert len(merged) == 2


def test_reduce_messages_replace_by_id():
    from langchain_core.messages import AIMessage
    left = [AIMessage(content="original", id="msg1")]
    right = [AIMessage(content="editado", id="msg1")]
    merged = reduce_messages(left, right)
    assert len(merged) == 1
    assert merged[0].content == "editado"
