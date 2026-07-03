"""
Ejemplo core de un agente con contexto de ejecución (`context_schema`) y salida estructurada tipada.

Extiende el patrón de `01_agentes_core.py` añadiendo `Context` (datos de la
petición, p. ej. `user_id`) como `context_schema` del agente, y genera un
`thread_id` distinto en cada ejecución con `uuid7()` en vez de usar un literal
fijo.

Ejemplo de ejecución:

    $ python 01agentes/02_agentes_core_context.py
    11:16:46 [INFO] agentes_core: Creando agente
    11:16:46 [INFO] agentes_core: Invocando agente (thread_id=019f2744-2a73-7bf0-a2f8-2ac71e040abd)
    11:16:50 [INFO] agentes_core: Respuesta estructurada: summary='¡Saludos! Soy un asistente de IA
    disponible para ayudarte con búsquedas de información y responder tus preguntas...' confidence=0.95

Cada ejecución genera un `thread_id` distinto (UUIDv7), por lo que no se
reutiliza memoria de checkpointer entre invocaciones.
"""

import logging
import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from uuid_utils import uuid7

import utils.logger
from utils.agents import build_chat_model, invoke_agent

load_dotenv()

logger = logging.getLogger("agentes_core")
utils.logger.configure_logging(logger, "INFO")

SYSTEM_PROMPT = "Eres un asistente muy útil. Sé conciso y preciso."
MODELO_HAIKU = "claude-haiku-4-5-20251001"
CONTENT = "Saludos desde un agente"


class Answer(BaseModel):
    """Salida estructurada esperada del agente.

    Attributes:
        summary: Resumen conciso de la respuesta del agente.
        confidence: Confianza del agente en la respuesta, entre 0.0 y 1.0.
    """

    summary: str
    confidence: float

@dataclass
class Context:
    """Contexto de ejecución del agente: datos de la petición, no del historial de conversación.

    Attributes:
        user_id: Identificador del usuario que realiza la petición.
    """

    user_id: str

@tool
def search(query: str) -> str:
    """Buscar información."""
    return f"Resultados para: {query}"


def build_agent(model, checkpointer):
    """Crea un agente con la tool `search` y salida estructurada tipada (`Answer`)."""
    logger.info("Creando agente")
    return create_agent(
        model=model,
        tools=[search],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        response_format=Answer,
        context_schema=Context,
    )


def main():
    """Invoca el agente y muestra su salida ya parseada como `Answer`, no el JSON crudo del mensaje."""
    model = build_chat_model(MODELO_HAIKU)
    checkpointer = InMemorySaver()

    agent = build_agent(model, checkpointer)

    thread_id = str(uuid7())
    logger.info("Invocando agente (thread_id=%s)", thread_id)
    result = invoke_agent(
        agent,
        CONTENT,
        thread_id,
        label="core",
        logger=logger,
        context=Context(user_id="user-123"),
    )

    if result is not None:
        answer: Answer = result["structured_response"]
        logger.info("Respuesta estructurada: summary=%r confidence=%.2f", answer.summary, answer.confidence)


if __name__ == "__main__":
    main()
