"""
Ejemplo core de invocación de un modelo de chat con mensajes tipados.

Construye el historial de conversación a mano combinando los tres tipos de
mensaje de `langchain.messages`: `SystemMessage` (instrucción del sistema),
`HumanMessage` (turno del usuario) y `AIMessage` (turno del modelo). El
`AIMessage` se inserta directamente en la lista, como si viniera de una
respuesta anterior del modelo, sin invocar el modelo para generarlo. Al
invocar con `model.invoke(messages)`, el modelo responde en función de todo
el historial, no solo del último mensaje.

Ejemplo de ejecución:

    $ python 03mensajes/01_mensajes.py
    13:26:37 [INFO] mensajes: Invocando modelo con 4 mensajes
    13:26:39 [INFO] mensajes: Respuesta: ¡Fácil! **2 + 2 = 4**
    ¿Hay algo más en lo que pueda ayudarte?
    13:26:39 [INFO] mensajes: Tokens: {'input_tokens': 72, 'output_tokens': 38, 'total_tokens': 110,
    'input_token_details': {'cache_creation': 0, 'cache_read': 0}}
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain.messages import AIMessage, HumanMessage, SystemMessage

import utils.logger
from utils.agents import build_chat_model

load_dotenv()

logger = logging.getLogger("mensajes")
utils.logger.configure_logging(logger, "INFO")

MODELO_HAIKU = "claude-haiku-4-5-20251001"


def build_messages() -> list[SystemMessage | HumanMessage | AIMessage]:
    """Construye un historial de conversación con los tres tipos de mensaje."""
    ai_msg = AIMessage("¡Encantado de ayudarte con esa pregunta!")
    return [
        SystemMessage("Eres un asistente muy útil."),
        HumanMessage("¿Puedes ayudarme?", name="Usuario", id="msg_123"),
        ai_msg,  # Insertado como si viniera del modelo en un turno anterior.
        HumanMessage("¡Genial! ¿Cuánto es 2+2?"),
    ]


def main():
    """Invoca el modelo con el historial de mensajes y loggea la respuesta."""
    model = build_chat_model(MODELO_HAIKU)
    messages = build_messages()

    logger.info("Invocando modelo con %d mensajes", len(messages))
    try:
        response = model.invoke(messages)
    except Exception:
        logger.exception("Fallo al invocar el modelo")
        return

    logger.info("Respuesta: %s", response.text)
    logger.info("Tokens: %s", response.usage_metadata)


if __name__ == "__main__":
    main()
