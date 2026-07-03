"""
Ejemplo core de un modelo de chat con tools vinculadas (`bind_tools`).

Extiende `01_mensajes.py`: en vez de invocar el modelo directamente, lo hace
a través de `model.bind_tools([search])`, que le da la capacidad de emitir
llamadas a `search` en vez de (o además de) responder con texto. La
respuesta se inspecciona en `response.tool_calls` (nombre, argumentos e id
de cada llamada) en lugar de asumir que `response.text` contiene siempre la
respuesta final: con Anthropic, un turno que solo llama a una tool devuelve
texto vacío.

Ejemplo de ejecución:

    $ python 03mensajes/02_mensajes_herramientas.py
    14:07:40 [INFO] mensajes_herramientas: Invocando modelo con tools vinculadas (2 mensajes)
    14:07:41 [INFO] mensajes_herramientas: Tool: search
    14:07:41 [INFO] mensajes_herramientas: Args: {'query': 'últimas noticias LangChain'}
    14:07:41 [INFO] mensajes_herramientas: ID: toolu_01TEkkhco7QvA42TVs98RxeN
    14:07:41 [INFO] mensajes_herramientas: Respuesta:
    14:07:41 [INFO] mensajes_herramientas: Tokens: {'input_tokens': 589, 'output_tokens': 60, 'total_tokens': 649,
    'input_token_details': {'cache_creation': 0, 'cache_read': 0}}
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool

import utils.logger
from utils.agents import build_chat_model

load_dotenv()

logger = logging.getLogger("mensajes_herramientas")
utils.logger.configure_logging(logger, "INFO")

MODELO_HAIKU = "claude-haiku-4-5-20251001"


@tool
def search(query: str) -> str:
    """Buscar información."""
    return f"Resultados para: {query}"


def build_messages() -> list[SystemMessage | HumanMessage]:
    """Construye un historial cuya pregunta requiere invocar la tool `search`."""
    return [
        SystemMessage("Eres un asistente muy útil."),
        HumanMessage("Busca información sobre las últimas noticias de LangChain."),
    ]


def main():
    """Invoca el modelo con tools vinculadas y loggea las llamadas a tools y la respuesta."""
    model = build_chat_model(MODELO_HAIKU)
    messages = build_messages()

    logger.info("Invocando modelo con tools vinculadas (%d mensajes)", len(messages))
    try:
        response = model.bind_tools([search]).invoke(messages)
    except Exception:
        logger.exception("Fallo al invocar el modelo")
        return

    for tool_call in response.tool_calls:
        logger.info("Tool: %s", tool_call["name"])
        logger.info("Args: %s", tool_call["args"])
        logger.info("ID: %s", tool_call["id"])

    logger.info("Respuesta: %s", response.text)
    logger.info("Tokens: %s", response.usage_metadata)


if __name__ == "__main__":
    main()
