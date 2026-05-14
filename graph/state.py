from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage


def reduce_messages(
    left: List[BaseMessage], right: List[BaseMessage]
) -> List[BaseMessage]:
    """Substitui mensagens pelo ID quando houver match, senao anexa.

    Essencial para a Etapa 3 (Human in the Loop com edicao):
    quando o moderador edita a justificativa, queremos SUBSTITUIR
    a mensagem do revisor em vez de anexar uma nova.
    """
    left_by_id = {getattr(m, "id", None): i for i, m in enumerate(left) if getattr(m, "id", None)}
    merged = list(left)
    for msg in right:
        mid = getattr(msg, "id", None)
        if mid and mid in left_by_id:
            merged[left_by_id[mid]] = msg
        else:
            merged.append(msg)
    return merged


class AgentState(TypedDict):
    """Estado compartilhado entre todos os agentes do grafo."""
    comentario_original: str
    politicas_relevantes: str
    analise_do_agente: str
    status_da_moderacao: str      # Aprovado | Problematico | Removido | Editado | Cancelado
    justificativa_final: str
    messages: Annotated[List[BaseMessage], reduce_messages]
