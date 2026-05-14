# ============================================================
# Sistema de Moderacao de Conteudo Assistido por IA
# Multi-agentes com LangGraph + Human in the Loop
# ============================================================

import asyncio
import uuid
import sys
import os

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from graph.builder import build_graph

load_dotenv()

# Valida chaves antes de iniciar
for key in ("OPENAI_API_KEY", "TAVILY_API_KEY"):
    val = os.getenv(key, "")
    if not val or val == "sua_chave_aqui":
        print(f"Erro: {key} nao configurada no .env")
        sys.exit(1)


# Comentarios de exemplo para demonstracao
EXEMPLOS = [
    "Excelente aula, professor! Aprendi muito sobre redes neurais.",
    "Compre seguidores baratos em meusite.com, preco imperdivel!!!",
    "Esse conteudo e meio fraco comparado ao outro curso que fiz.",
    "Voce e burro demais pra ensinar, va fazer outra coisa da vida.",
    "Alguem tem o PDF pirata do livro que o professor indicou?",
]


async def run():
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as memory:
        graph = build_graph(memory)

        # Gera diagrama do grafo (se possivel)
        try:
            mermaid = graph.get_graph().draw_mermaid()
            with open("grafo.mmd", "w") as f:
                f.write(mermaid)
            print("Diagrama salvo em grafo.mmd")
        except Exception:
            pass

        print("\n" + "=" * 60)
        print("SISTEMA DE MODERACAO DE CONTEUDO — IA + Human in the Loop")
        print("=" * 60)

        print("\nExemplos disponiveis:")
        for i, ex in enumerate(EXEMPLOS, 1):
            print(f"  {i}. {ex[:60]}...")

        escolha = input("\nEscolha um numero (1-5) ou digite um comentario: ").strip()

        if escolha.isdigit() and 1 <= int(escolha) <= len(EXEMPLOS):
            comentario = EXEMPLOS[int(escolha) - 1]
        else:
            comentario = escolha

        print(f"\nComentario a moderar: \"{comentario}\"")
        print("-" * 60)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {"comentario_original": comentario, "messages": []}

        # --- Executa ate a interrupcao ---
        async for event in graph.astream(initial_state, config):
            for node, payload in event.items():
                if node == "__end__":
                    continue
                print(f"\n[AGENTE: {node}]")
                for k, v in payload.items():
                    if k != "messages":
                        print(f"  {k}: {str(v)[:300]}")

        # --- Verifica se ha interrupcao (HITL) ---
        snapshot = await graph.aget_state(config)

        if not snapshot.next:
            # Fluxo terminou sem interrupcao (comentario aprovado automaticamente)
            print("\nComentario aprovado automaticamente (nenhum problema detectado).")
            return

        # --- Etapa 2 + 3: Intervencao humana ---
        print("\n" + "=" * 60)
        print("PAUSA PARA REVISAO HUMANA")
        print("=" * 60)
        print(f"\nRecomendacao do agente:\n{snapshot.values.get('justificativa_final', '')}")
        print(f"\nAnalise: {snapshot.values.get('analise_do_agente', '')[:200]}")
        print("-" * 60)

        decisao = input("\nEscolha: [sim] confirmar | [nao] cancelar | [editar] modificar: ").strip().lower()

        if decisao == "editar":
            # Etapa 3: moderador edita o estado diretamente
            nova_just = input("Digite a nova justificativa final: ")
            novo_status = input("Novo status (Aprovado/Removido/Editado): ").strip()
            if novo_status not in ("Aprovado", "Removido", "Editado"):
                novo_status = "Editado"
            await graph.aupdate_state(
                config,
                {
                    "justificativa_final": nova_just,
                    "status_da_moderacao": novo_status,
                },
            )
            print("\nEstado atualizado com intervencao humana.")

        elif decisao == "nao":
            await graph.aupdate_state(
                config,
                {
                    "status_da_moderacao": "Cancelado pelo moderador",
                    "justificativa_final": "Acao cancelada manualmente pelo moderador.",
                },
            )

        # --- Retoma execucao ---
        async for event in graph.astream(None, config):
            for node, payload in event.items():
                if node == "__end__":
                    continue
                print(f"\n[CONTINUACAO - AGENTE: {node}]")

        print("\nModeracao concluida.")


if __name__ == "__main__":
    asyncio.run(run())
