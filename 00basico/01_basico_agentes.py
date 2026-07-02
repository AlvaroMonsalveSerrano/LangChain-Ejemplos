"""
Ejemplo básico y simple de creación de un agente.

"""


import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain.agents import create_agent
import utils.logger

load_dotenv()

logger = logging.getLogger("subagents")
utils.logger.configure_logging(logger, "INFO")


def get_weather(city: str) -> str:
    """Obtén el pronóstico del tiempo para una ciudad determinada."""
    return f"Siempre hace sol en {city}!"

agent = create_agent(
    model="claude-haiku-4-5-20251001",
    tools=[get_weather],
    system_prompt="Eres un asistente útil",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "¿Qué tiempo hace en Madrid?"}]}
)
print(result["messages"][-1].content_blocks)