"""
Ejemplo core de un agente con streaming de eventos.

Extiende el patrón de `01_agentes_core.py` sustituyendo la invocación
síncrona (`agent.invoke`) por `agent.stream(..., stream_mode="values")`,
que emite el estado completo del grafo (los mensajes acumulados) después
de cada paso. Esto permite mostrar en tiempo real cuándo el agente
responde con texto y cuándo decide llamar a una tool, en vez de esperar
al resultado final.

Ejemplo de ejecución:

    $ python 01agentes/03_agentes_streaming.py
    11:31:33 [INFO] agentes_streaming: Creando agente
    11:31:33 [INFO] agentes_streaming: Iniciando streaming (thread_id=019f2751-b115-71e2-a826-66df18bf7b95)
    11:31:33 [INFO] agentes_streaming: User: Busca noticias de IA y resume los hallazgos
    11:31:34 [INFO] agentes_streaming: Calling tools: ['search']
    11:31:38 [INFO] agentes_streaming: Agent: Lamento que la búsqueda no haya retornado resultados
    específicos. Sin embargo, puedo ofrecerte un resumen de las tendencias actuales en IA...
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from uuid_utils import uuid7

import utils.logger
from utils.agents import build_chat_model

load_dotenv()

logger = logging.getLogger("agentes_streaming")
utils.logger.configure_logging(logger, "INFO")

SYSTEM_PROMPT = "Eres un asistente muy útil. Sé conciso y preciso."
MODELO_HAIKU = "claude-haiku-4-5-20251001"
CONTENT = "Busca noticias de IA y resume los hallazgos"


@tool
def search(query: str) -> str:
    """Buscar información."""
    return f"Resultados para: {query}"


def build_agent(model, checkpointer):
    """Crea un agente con la tool `search` para el ejemplo de streaming."""
    logger.info("Creando agente")
    return create_agent(
        model=model,
        tools=[search],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


def stream_agent(agent, content, thread_id):
    """Recorre el streaming de estados del agente y loggea cada paso según su tipo.

    Cada `snapshot` es el estado completo del grafo tras un paso
    (`stream_mode="values"`): el último mensaje puede ser el del usuario,
    una llamada a tool o el texto de respuesta del agente.
    """
    stream = agent.stream(
        {"messages": [{"role": "user", "content": content}]},
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="values",
    )
    for snapshot in stream:
        latest_message = snapshot["messages"][-1]
        if isinstance(latest_message, AIMessage) and latest_message.tool_calls:
            logger.info("Calling tools: %s", [tc["name"] for tc in latest_message.tool_calls])
        elif isinstance(latest_message, HumanMessage) and latest_message.content:
            logger.info("User: %s", latest_message.content)
        elif isinstance(latest_message, AIMessage) and latest_message.content:
            logger.info("Agent: %s", latest_message.text)


def main():
    """Crea el agente y loggea cada paso del streaming (usuario, tool calls, respuesta)."""
    model = build_chat_model(MODELO_HAIKU)
    checkpointer = InMemorySaver()

    agent = build_agent(model, checkpointer)

    thread_id = str(uuid7())
    logger.info("Iniciando streaming (thread_id=%s)", thread_id)
    try:
        stream_agent(agent, CONTENT, thread_id)
    except Exception:
        logger.exception("Fallo al hacer streaming del agente (thread_id=%s)", thread_id)


if __name__ == "__main__":
    main()
