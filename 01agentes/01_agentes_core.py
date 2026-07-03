"""
Ejemplo core de un agente con una tool y salida estructurada tipada.

Crea un agente con `create_agent` que dispone de la tool `search` y usa
`response_format=Answer` (modelo Pydantic) para obtener una respuesta
estructurada y validada en vez de texto libre.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

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
    )


def main():
    """Invoca el agente y muestra su salida ya parseada como `Answer`, no el JSON crudo del mensaje."""
    model = build_chat_model(MODELO_HAIKU)
    checkpointer = InMemorySaver()

    agent = build_agent(model, checkpointer)

    logger.info("Invocando agente (thread_id=agentes-core)")
    result = invoke_agent(agent, CONTENT, "agentes-core", label="core", logger=logger)

    if result is not None:
        answer: Answer = result["structured_response"]
        logger.info("Respuesta estructurada: summary=%r confidence=%.2f", answer.summary, answer.confidence)


if __name__ == "__main__":
    main()
