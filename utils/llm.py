import os
from langchain_openai import ChatOpenAI


def get_llm():
    """Retorna instancia do modelo configurada para moderacao."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sua_chave_aqui":
        raise ValueError(
            "OPENAI_API_KEY nao encontrada. "
            "Edite o arquivo .env com sua chave da OpenAI."
        )
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.2,
        request_timeout=30,
        max_retries=2,
    )
