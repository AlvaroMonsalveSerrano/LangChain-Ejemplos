"""Helpers compartidos para construir e invocar agentes de LangChain."""

from langchain.chat_models import init_chat_model


def build_chat_model(
    model_name,
    *,
    model_provider="anthropic",
    temperature=0.5,
    timeout=600,
    max_tokens=4096,
    streaming=True,
):
    """Crea un modelo de chat con los valores por defecto usados en los ejemplos del repo."""
    return init_chat_model(
        model_name,
        model_provider=model_provider,
        temperature=temperature,
        timeout=timeout,
        max_tokens=max_tokens,
        streaming=streaming,
    )


def invoke_agent(agent, content, thread_id, *, label, logger, context=None):
    """Invoca un agente capturando cualquier fallo de la llamada (red, API, rate limit)
    para que no tumbe el script completo ni impida intentar el resto de agentes.

    Args:
        context: Objeto de contexto de ejecución (p. ej. una instancia del
            `context_schema` registrado en `create_agent`). Se omite si es None.
    """
    try:
        return agent.invoke(
            {"messages": [{"role": "user", "content": content}]},
            config={"configurable": {"thread_id": thread_id}},
            context=context,
        )
    except Exception:
        logger.exception("Fallo al invocar el agente '%s' (thread_id=%s)", label, thread_id)
        return None
