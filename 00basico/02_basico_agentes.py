import ipaddress
import logging
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain.agents import create_agent
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

import utils.logger

load_dotenv()

logger = logging.getLogger("basico_agentes")
utils.logger.configure_logging(logger, "INFO")

SYSTEM_PROMPT = """Eres un asistente de datos literarios.

## Capacidades

- `fetch_text_from_url`: carga el texto de un documento desde una URL en la conversación.
No adivines el número de líneas ni las posiciones: básate en los resultados de las herramientas del fichero guardado."""

CONTENT = """Project Gutenberg aloja una copia completa en texto plano de El gran Gatsby de F. Scott Fitzgerald.
URL: https://www.gutenberg.org/files/64317/64317-0.txt

Responde con la mayor precisión posible:

1) Cuántas líneas del fichero completo de Gutenberg contienen la subcadena `Gatsby` (cuenta líneas, no apariciones dentro de una línea; cada línea termina con un salto de línea).
2) El número de línea (empezando en 1) de la primera línea del fichero que contiene `Daisy`.
3) Una sinopsis neutral de dos frases.

Haz todo lo posible en (1) y (2). Si en algún momento te das cuenta de que no puedes **verificar** una respuesta exacta con
las herramientas y el razonamiento disponibles, no inventes números: usa `null` para ese campo y explica
la limitación en `how_you_computed_counts`. Si encuentras algún error, indica cuál fue y cuál fue su mensaje."""


ALLOWED_URL_SCHEMES = {"http", "https"}


def _rejection_reason(url: str) -> str | None:
    """Devuelve el motivo de rechazo de la URL, o None si es segura de descargar.

    Bloquea esquemas distintos de http/https y hosts que resuelvan a IPs
    privadas, loopback, link-local o de otro modo no enrutables (RFC 1918,
    169.254.169.254 de metadata en la nube, localhost, etc.) para evitar que
    la tool se use como vector de SSRF.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        return f"esquema no permitido: {parsed.scheme!r}"
    if not parsed.hostname:
        return "la URL no tiene host"
    try:
        addrs = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror as e:
        return f"no se pudo resolver el host: {e}"
    for addr in addrs:
        ip = ipaddress.ip_address(addr)
        if not ip.is_global:
            return f"el host resuelve a una IP no pública ({addr})"
    return None


@tool
def fetch_text_from_url(url: str) -> str:
    """Obtiene el documento desde una URL.
    """
    reason = _rejection_reason(url)
    if reason is not None:
        logger.warning("URL rechazada por seguridad (%s): %s", reason, url)
        return f"Fetch rechazado: {reason}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        return f"Fetch failed: {e}"
    return raw.decode("utf-8", errors="replace")


def build_model():
    """Crea el modelo de chat de Claude Haiku usado por ambos agentes."""
    logger.info("Creando modelo Claude Haiku")
    return init_chat_model(
        "claude-haiku-4-5-20251001",
        model_provider="anthropic",
        temperature=0.5,
        timeout=600,
        max_tokens=4096,
        streaming=True,
    )


def build_agent(model, checkpointer):
    """Crea un agente estándar de LangChain con la tool de fetch."""
    logger.info("Creando agente estándar")
    return create_agent(
        model=model,
        tools=[fetch_text_from_url],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


def build_deep_agent(model, checkpointer):
    """Crea un deep agent (con planificación multi-paso) con la misma tool."""
    logger.info("Creando deep agent")
    return create_deep_agent(
        model=model,
        tools=[fetch_text_from_url],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


def _invoke_agent(agent, label, thread_id):
    """Invoca un agente capturando cualquier fallo de la llamada (red, API, rate limit)
    para que no tumbe el script completo ni impida intentar el resto de agentes."""
    try:
        return agent.invoke(
            {"messages": [{"role": "user", "content": CONTENT}]},
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception:
        logger.exception("Fallo al invocar el agente '%s' (thread_id=%s)", label, thread_id)
        return None


def main():
    """Ejecuta la misma consulta sobre The Great Gatsby con ambos agentes y compara resultados."""
    model = build_model()
    checkpointer = InMemorySaver()

    agent = build_agent(model, checkpointer)
    deep_agent = build_deep_agent(model, checkpointer)

    # Cada invocación usa un thread_id distinto para no compartir memoria entre agentes.
    logger.info("Invocando agente estándar (thread_id=great-gatsby-lc)")
    agent_result = _invoke_agent(agent, "estándar", "great-gatsby-lc")

    logger.info("Invocando deep agent (thread_id=great-gatsby-da)")
    deep_agent_result = _invoke_agent(deep_agent, "deep", "great-gatsby-da")

    if agent_result is not None:
        logger.info("Resultado del agente estándar: %s", agent_result["messages"][-1].content_blocks)
    if deep_agent_result is not None:
        logger.info("Resultado del deep agent: %s", deep_agent_result["messages"][-1].content_blocks)


if __name__ == "__main__":
    main()
