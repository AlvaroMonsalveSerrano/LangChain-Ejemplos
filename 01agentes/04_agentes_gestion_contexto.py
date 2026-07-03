"""
Ejemplo core de gestión de contexto mediante middleware de `deepagents`.

En vez de pasar contexto a mano (`context_schema`, como en
`02_agentes_core_context.py`), este módulo delega la gestión del contexto
del agente en middleware especializado, todo compartiendo el mismo backend:

- `FilesystemMiddleware`: da al agente tools de fichero (`read_file`,
  `write_file`, `edit_file`, `ls`) sobre el backend.
- `SummarizationMiddleware`: resume el historial de mensajes automáticamente
  cuando se acerca al límite de contexto del modelo.
- `MemoryMiddleware`: inyecta en el system prompt el contenido de ficheros
  de memoria persistente (`AGENTS.md`) leídos del backend.
- `SkillsMiddleware`: expone al agente un catálogo de "skills" (ficheros
  `SKILL.md` con instrucciones reutilizables) leídos del backend.

Se usa `FilesystemBackend` (en vez de `StateBackend`) apuntando a la carpeta
`01agentes/context/`, con `virtual_mode=True` para confinar el acceso a esa
carpeta (ningún path absoluto ni `..` puede escapar de `root_dir`). Con
`StateBackend` los ficheros viven solo en el estado del grafo, así que
`MemoryMiddleware`/`SkillsMiddleware` no tendrían nada que cargar salvo que
el propio agente los escribiera antes con las tools de fichero.

Estructura de `01agentes/context/`:

    context/
    ├── AGENTS.md                        # Memoria: cargada por MemoryMiddleware
    └── skills/
        └── resumen-conciso/
            └── SKILL.md                 # Skill: catalogada por SkillsMiddleware

Ejemplo de ejecución:

    $ python 01agentes/04_agentes_gestion_contexto.py
    11:49:18 [INFO] agentes_gestion_contexto: Creando agente con middleware de contexto
    11:49:18 [INFO] agentes_gestion_contexto: Invocando agente (thread_id=019f2761-f315-7841-a046-97a94c52c928)
    11:49:21 [INFO] agentes_gestion_contexto: Respuesta: Según mi información actual:
    **Skills disponibles:** resumen-conciso: resumir resultados en máximo tres frases, en español.
    **Memoria sobre idioma preferido:** el usuario prefiere respuestas en español, concisas y sin relleno.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from deepagents.backends import FilesystemBackend
from deepagents.middleware import (
    FilesystemMiddleware,
    MemoryMiddleware,
    SkillsMiddleware,
    SummarizationMiddleware,
)
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from uuid_utils import uuid7

import utils.logger
from utils.agents import build_chat_model, invoke_agent

load_dotenv()

logger = logging.getLogger("agentes_gestion_contexto")
utils.logger.configure_logging(logger, "INFO")

SYSTEM_PROMPT = "Eres un asistente muy útil. Sé conciso y preciso."
MODELO_HAIKU = "claude-haiku-4-5-20251001"
CONTENT = "¿Qué skill tienes disponible y qué dice tu memoria sobre el idioma preferido?"
CONTEXT_DIR = Path(__file__).parent / "context"


@tool
def search(query: str) -> str:
    """Buscar información."""
    return f"Resultados para: {query}"


def build_agent(model, checkpointer):
    """Crea un agente cuya gestión de contexto delega en middleware sobre un backend compartido."""
    logger.info("Creando agente con middleware de contexto")
    backend = FilesystemBackend(root_dir=CONTEXT_DIR, virtual_mode=True)
    return create_agent(
        model=model,
        tools=[search],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        middleware=[
            FilesystemMiddleware(backend=backend),
            SummarizationMiddleware(model=model, backend=backend),
            MemoryMiddleware(backend=backend, sources=["AGENTS.md"]),
            SkillsMiddleware(backend=backend, sources=["skills"]),
        ],
    )


def main():
    """Invoca el agente y muestra la respuesta, ya informada por memoria y skills."""
    model = build_chat_model(MODELO_HAIKU)
    checkpointer = InMemorySaver()

    agent = build_agent(model, checkpointer)

    thread_id = str(uuid7())
    logger.info("Invocando agente (thread_id=%s)", thread_id)
    result = invoke_agent(agent, CONTENT, thread_id, label="gestion-contexto", logger=logger)

    if result is not None:
        logger.info("Respuesta: %s", result["messages"][-1].text)


if __name__ == "__main__":
    main()
