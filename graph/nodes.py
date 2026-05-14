import logging
import os
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_tavily import TavilySearch

log = logging.getLogger(__name__)

from utils.llm import get_llm
from graph.state import AgentState


# Carrega diretrizes do arquivo
_dir = Path(__file__).resolve().parent.parent / "policies" / "diretrizes.txt"
DIRETRIZES = _dir.read_text(encoding="utf-8") if _dir.exists() else ""

# Lazy init: evita chamar get_llm() antes do load_dotenv() no main.py
_llm = None


def _get_llm():
    """Retorna o LLM, inicializando na primeira chamada (singleton lazy)."""
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm


def agente_analisador(state: AgentState) -> dict:
    """Analisa o comentario e classifica como POSITIVO, NEUTRO ou PROBLEMATICO."""
    prompt = f"""Analise o comentario de um aluno em uma plataforma de cursos online.
Classifique como: POSITIVO, NEUTRO ou PROBLEMATICO.
Se for PROBLEMATICO, indique a categoria (spam, ofensivo, irrelevante, pirataria, privacidade).

Comentario: "{state['comentario_original']}"

Responda EXATAMENTE neste formato:
CLASSIFICACAO: <POSITIVO|NEUTRO|PROBLEMATICO>
CATEGORIA: <categoria ou N/A>
JUSTIFICATIVA: <breve analise em 1-2 frases>"""

    try:
        resp = _get_llm().invoke(prompt)
        analise = resp.content
    except Exception:
        analise = "CLASSIFICACAO: PROBLEMATICO\nCATEGORIA: erro\nJUSTIFICATIVA: Falha na analise. Encaminhado para revisao humana."

    status = "Problematico" if "PROBLEMATICO" in analise.upper() else "Aprovado"

    return {
        "analise_do_agente": analise,
        "status_da_moderacao": status,
    }


def agente_pesquisador_politicas(state: AgentState) -> dict:
    """Busca politicas relevantes nas diretrizes internas + contexto externo."""
    # Busca complementar com Tavily
    externo = ""
    try:
        search_tool = TavilySearch(max_results=2)
        query = f"politica moderacao comentarios comunidade online {state['analise_do_agente'][:80]}"
        resultados = search_tool.invoke(query)
        if isinstance(resultados, list):
            externo = "\n".join([
                r.get("content", "")[:200] if isinstance(r, dict) else str(r)[:200]
                for r in resultados[:2]
            ])
        else:
            externo = str(resultados)[:400]
    except Exception:
        externo = "(busca externa indisponivel)"

    politicas = f"DIRETRIZES INTERNAS:\n{DIRETRIZES}\n\nCONTEXTO EXTERNO:\n{externo}"
    return {"politicas_relevantes": politicas}


def agente_revisor(state: AgentState) -> dict:
    """Consolida analise + politicas e recomenda acao final."""
    prompt = f"""Voce e um moderador de conteudo. Com base na analise e nas politicas,
recomende uma acao para o comentario.

Comentario original: "{state['comentario_original']}"

Analise do agente: {state['analise_do_agente']}

Politicas aplicaveis: {state['politicas_relevantes'][:500]}

Recomende UMA acao: APROVAR | REMOVER | EDITAR
Justifique em 1-2 frases, citando a politica violada quando aplicavel.

Responda EXATAMENTE neste formato:
ACAO: <APROVAR|REMOVER|EDITAR>
JUSTIFICATIVA: <texto>"""

    try:
        resp = _get_llm().invoke(prompt)
        conteudo = resp.content
    except Exception:
        conteudo = "ACAO: REMOVER\nJUSTIFICATIVA: Erro na revisao. Recomendado revisao humana."

    return {
        "justificativa_final": conteudo,
        "messages": [AIMessage(content=conteudo, id="revisor_msg")],
    }


def executar_acao_final(state: AgentState) -> dict:
    """Executa a acao final (no real world: atualiza banco de dados)."""
    log.info("ACAO EXECUTADA — Status: %s | Justificativa: %s",
             state['status_da_moderacao'], state['justificativa_final'])
    return {}
