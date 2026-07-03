"""
Ejemplo core de planificación y delegación mediante middleware de `deepagents`.

Añade a un agente dos capacidades que no requieren código propio, solo
middleware:

- `TodoListMiddleware` (de `langchain.agents.middleware`): da al agente la
  tool `write_todos` para planificar objetivos complejos en pasos y marcar
  su progreso, en vez de intentar resolverlo todo en una sola respuesta.
- `SubAgentMiddleware` (de `deepagents.middleware.subagents`): da al agente
  la tool `task` para delegar un subobjetivo en un subagente efímero
  (`researcher`) con su propio system prompt, tools y modelo. El subagente
  corre de forma aislada y solo devuelve un resultado final al agente
  orquestador, sin exponerle sus pasos intermedios.

Ambos middleware comparten un `StateBackend` con `FilesystemMiddleware`, que
da al agente y al subagente tools de fichero (`read_file`, `write_file`,
`edit_file`, `ls`) sobre un sistema de ficheros virtual en el propio estado
del grafo (no toca disco), útil aquí como bloc de notas compartido entre el
orquestador y sus subagentes.

Ejemplo de ejecución:

    $ python 01agentes/05_agentes_planificacion_delegacion.py
    11:58:28 [INFO] agentes_planificacion_delegacion: Creando agente con planificación y delegación
    11:58:28 [INFO] agentes_planificacion_delegacion: Invocando agente (thread_id=019f276a-57e9-7b80-884d-643328e889f5)
    11:59:06 [INFO] agentes_planificacion_delegacion: Respuesta: ## Resumen de Tendencias en IA Generativa
    El subagente ha completado una investigación exhaustiva. Aquí están los hallazgos principales...
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from deepagents.backends import StateBackend
from deepagents.middleware import FilesystemMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from uuid_utils import uuid7

import utils.logger
from utils.agents import build_chat_model, invoke_agent

load_dotenv()

logger = logging.getLogger("agentes_planificacion_delegacion")
utils.logger.configure_logging(logger, "INFO")

SYSTEM_PROMPT = "Eres un asistente muy útil. Sé conciso y preciso."
MODELO_HAIKU = "claude-haiku-4-5-20251001"
CONTENT = (
    "Investiga las tendencias más importantes en IA generativa y resume los "
    "hallazgos. Delega la búsqueda a un subagente."
)


@tool
def search(query: str) -> str:
    """Search for a query and return a short summary."""
    return f"Search results for: {query}"


def build_agent(model, checkpointer):
    """Crea un agente que planifica con `TodoListMiddleware` y delega con `SubAgentMiddleware`."""
    logger.info("Creando agente con planificación y delegación")
    backend = StateBackend()
    researcher = {
        "name": "researcher",
        "description": "Busca información y devuelve un resumen estructurado.",
        "system_prompt": "Usa la tool search para investigar la pregunta y resume los puntos clave.",
        "tools": [search],
        "model": model,
        "middleware": [],
    }
    return create_agent(
        model=model,
        tools=[search],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        middleware=[
            FilesystemMiddleware(backend=backend),
            TodoListMiddleware(),
            SubAgentMiddleware(backend=backend, subagents=[researcher]),
        ],
    )


def main():
    """Invoca el agente y muestra la respuesta final, ya sintetizada a partir del subagente."""
    model = build_chat_model(MODELO_HAIKU)
    checkpointer = InMemorySaver()

    agent = build_agent(model, checkpointer)

    thread_id = str(uuid7())
    logger.info("Invocando agente (thread_id=%s)", thread_id)
    result = invoke_agent(agent, CONTENT, thread_id, label="planificacion-delegacion", logger=logger)

    if result is not None:
        logger.info("Respuesta: %s", result["messages"][-1].text)


if __name__ == "__main__":
    main()
