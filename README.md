# Ejem1-LangChain

Sandbox de pruebas conceptuales con la librería [LangChain](https://python.langchain.com/) (agentes, `deepagents`, modelos, mensajería y herramientas). Cada módulo es un script autocontenido que demuestra un concepto concreto del ecosistema.

---

## Estructura del proyecto

```
.
├── 00basico/          # Módulos desarrollados: creación de agentes
├── 01agentes/         # Módulos desarrollados: tools, contexto, streaming, middleware y subagentes
│   └── context/       # Memoria (AGENTS.md) y skills usados por 04_agentes_gestion_contexto.py
├── 02modelos/         # Pendiente de desarrollo
├── 03mensajes/        # Módulos desarrollados: mensajes tipados y tools vinculadas
├── 04herramientas/    # Pendiente de desarrollo
├── utils/
│   ├── agents.py      # Helpers compartidos: construcción de modelo e invocación de agentes
│   └── logger.py      # Configuración de logging compartida entre módulos
├── requirements.txt
└── CLAUDE.md           # Orientación específica para Claude Code
```

Cada carpeta numerada agrupa módulos de un mismo tema. `00basico/`, `01agentes/` y `03mensajes/` ya tienen módulos implementados (ver [Módulos desarrollados](#módulos-desarrollados)); `02modelos/` y `04herramientas/` siguen siendo carpetas reservadas para próximos ejemplos.

---

## Instalación del entorno

**Requisitos:** Python 3.10+

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar credenciales
# No existe .env.example en el repo: crea un fichero .env en la raíz
# con las variables necesarias (ver la siguiente sección).
```

> **Nota (macOS x86_64):** una de las dependencias transitivas (`cbor2`, usada por `modal`) no publica wheel precompilada para macOS x86_64 en versiones recientes, y compilarla desde fuente requiere un compilador de Rust. Si `pip install -r requirements.txt` falla con `error: can't find Rust compiler`, instala antes una versión con wheel disponible: `pip install "cbor2==5.7.1"`.

---

## Variables de entorno

El fichero `.env` (no versionado, ver `.gitignore`) debe definirse en la raíz del proyecto. Estas son las variables relevantes para este repositorio:

| Variable | Usada por | Descripción |
|----------|-----------|-------------|
| `ANTHROPIC_API_KEY` | Todos los módulos de `00basico/`, `01agentes/` y `03mensajes/` | Credencial de Anthropic; los agentes actuales usan Claude Haiku. |
| `OPENAI_API_KEY` | Declarada como dependencia (`langchain-openai`) pero ningún módulo actual la usa todavía. | Necesaria si un módulo futuro usa modelos de OpenAI. |
| `TAVILY_API_KEY` | Declarada como dependencia (`tavily-python`) pero ningún módulo actual la usa todavía. | Necesaria si un módulo futuro añade búsqueda web con Tavily. |
| `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`, `LANGSMITH_PROJECT` | Opcional, vía `utils/logger.py` | Activan trazas remotas en LangSmith cuando se configuran; si se omiten, el logging queda solo en local (stdout). |

---

## Módulos desarrollados

### `00basico/`

| Módulo | Descripción |
|--------|-------------|
| [`00basico/01_basico_agentes.py`](00basico/01_basico_agentes.py) | Ejemplo mínimo de agente con `create_agent` de LangChain. Define una tool simple (`get_weather`), usa Claude Haiku como modelo y registra trazas con `utils/logger.py`. |
| [`00basico/02_basico_agentes.py`](00basico/02_basico_agentes.py) | Compara un agente estándar (`create_agent`) frente a un deep agent (`create_deep_agent` de `deepagents`) sobre la misma tarea: analizar el texto completo de *El gran Gatsby* descargado desde Project Gutenberg mediante la tool `fetch_text_from_url`. Incluye: checkpointer en memoria compartido entre ambos agentes (con `thread_id` distinto por agente), validación anti-SSRF en la tool de descarga (solo esquemas `http`/`https` y bloqueo de IPs privadas, loopback y link-local), manejo de errores en las invocaciones para que el fallo de un agente no impida ejecutar el otro, y logging estructurado con `utils/logger.py`. |

### `01agentes/`

| Módulo | Descripción |
|--------|-------------|
| [`01agentes/01_agentes_core.py`](01agentes/01_agentes_core.py) | Agente core con una tool (`search`) y salida estructurada tipada vía `response_format=Answer` (modelo Pydantic). El resultado parseado se lee de `result["structured_response"]`, no del texto crudo del último mensaje. |
| [`01agentes/02_agentes_core_context.py`](01agentes/02_agentes_core_context.py) | Extiende `01_agentes_core.py` añadiendo contexto de ejecución vía `context_schema=Context` (datos de la petición, p. ej. `user_id`, distintos del historial de conversación) y genera un `thread_id` nuevo por ejecución con `uuid7()`. |
| [`01agentes/03_agentes_streaming.py`](01agentes/03_agentes_streaming.py) | Sustituye la invocación síncrona (`agent.invoke`) por streaming con `agent.stream(..., stream_mode="values")`, que emite el estado completo del grafo tras cada paso. Distingue y loggea en tiempo real el mensaje del usuario, las llamadas a tools y el texto final del agente. |
| [`01agentes/04_agentes_gestion_contexto.py`](01agentes/04_agentes_gestion_contexto.py) | Gestiona el contexto del agente con middleware de `deepagents` en vez de código propio: `FilesystemMiddleware` (tools de fichero), `SummarizationMiddleware` (resumen automático del historial), `MemoryMiddleware` (memoria persistente desde `AGENTS.md`) y `SkillsMiddleware` (catálogo de skills desde ficheros `SKILL.md`). Usa `FilesystemBackend` con `virtual_mode=True` apuntando a [`01agentes/context/`](01agentes/context/) para que memoria y skills carguen contenido real. |
| [`01agentes/05_agentes_planificacion_delegacion.py`](01agentes/05_agentes_planificacion_delegacion.py) | Añade planificación con `TodoListMiddleware` (tool `write_todos` para descomponer objetivos complejos en pasos) y delegación con `SubAgentMiddleware` (tool `task` para lanzar un subagente `researcher` efímero con su propia tool, system prompt y modelo). Ambos comparten un `StateBackend` con `FilesystemMiddleware` como bloc de notas virtual entre el orquestador y sus subagentes. |

Los cinco módulos de `01agentes/` comparten `utils/agents.py::build_chat_model()` para construir el modelo de chat con los valores por defecto del repo; todos salvo `03_agentes_streaming.py` (streaming, invocación como generador) reutilizan también `utils/agents.py::invoke_agent()` para invocar el agente con manejo de errores homogéneo.

### `03mensajes/`

| Módulo | Descripción |
|--------|-------------|
| [`03mensajes/01_mensajes.py`](03mensajes/01_mensajes.py) | Invoca un modelo de chat directamente (sin `create_agent`) con un historial construido a mano combinando `SystemMessage`, `HumanMessage` y `AIMessage` de `langchain.messages`. Loggea la respuesta y `response.usage_metadata` (tokens de entrada, salida y total). |
| [`03mensajes/02_mensajes_herramientas.py`](03mensajes/02_mensajes_herramientas.py) | Extiende `01_mensajes.py` vinculando una tool al modelo con `model.bind_tools([search])` en vez de usar un agente. Inspecciona `response.tool_calls` (nombre, argumentos e id de cada llamada) en vez de asumir que `response.text` trae la respuesta final, ya que un turno que solo llama a una tool devuelve texto vacío. |

A diferencia de `01agentes/`, los módulos de `03mensajes/` invocan el modelo de chat directamente (`model.invoke(...)` / `model.bind_tools(...).invoke(...)`), sin pasar por `create_agent`; ambos reutilizan `utils/agents.py::build_chat_model()`.

---

## Convenciones observadas en los módulos actuales

- Nomenclatura `NN_nombre_concepto.py` dentro de una carpeta temática numerada (p. ej. `00basico/`, `01agentes/`).
- Cada módulo añade la raíz del proyecto a `sys.path` (`sys.path.insert(0, str(Path(__file__).parent.parent))`) **antes** de importar `utils`, y carga credenciales con `python-dotenv` (`load_dotenv()`).
- Logging homogéneo vía `utils/logger.py`: `logger = logging.getLogger("<nombre>")` seguido de `utils.logger.configure_logging(logger, "INFO")`. Nunca `print` para resultados o trazas.
- La lógica se encapsula en funciones (`build_*`, `main`) con guardia `if __name__ == "__main__": main()`, en vez de código suelto a nivel de módulo.
- La construcción del modelo de chat y la invocación de agentes con manejo de errores se centralizan en `utils/agents.py` (`build_chat_model()`, `invoke_agent()`) para no duplicar ese boilerplate entre módulos.
- Modelo por defecto: `claude-haiku-4-5-20251001` vía `model_provider="anthropic"`.

---

## Cómo ejecutar los módulos

```bash
# Activar el entorno virtual si no está activo
source .venv/bin/activate

# Ejecutar un módulo concreto
python 00basico/01_basico_agentes.py
python 01agentes/03_agentes_streaming.py

# Ejecutar todos los módulos de una carpeta en orden
for f in 00basico/0*.py; do echo "=== $f ==="; python "$f"; done
for f in 01agentes/0*.py; do echo "=== $f ==="; python "$f"; done
for f in 03mensajes/0*.py; do echo "=== $f ==="; python "$f"; done
```

> Todos los módulos loggean su resultado por stdout (nunca `print`). Asegúrate de que `.env` está configurado antes de ejecutarlos.

---

## Tests

🚧 **Pendiente:** todavía no hay ningún test implementado ni carpeta `tests/` en el repo.

El patrón previsto (documentado en `CLAUDE.md`) es usar `pytest` con un LLM simulado (`FakeListLLM`) para no depender de llamadas reales a la API ni de credenciales, con ficheros en `tests/` siguiendo la convención `test_<nombre_del_módulo>.py`.

---

## Estado del proyecto

- ✅ `00basico/` — 2 módulos de agentes implementados y verificados.
- ✅ `01agentes/` — 5 módulos implementados y verificados: tool + salida estructurada, contexto de ejecución, streaming, gestión de contexto por middleware, y planificación + delegación en subagentes.
- ✅ `03mensajes/` — 2 módulos implementados y verificados: mensajes tipados (`SystemMessage`/`HumanMessage`/`AIMessage`) y tools vinculadas con `bind_tools`.
- 🚧 `02modelos/`, `04herramientas/` — carpetas creadas, sin contenido todavía.
- 🚧 `tests/` — sin implementar.

---

## Licencia

Este repositorio no tiene una licencia definida todavía (sandbox de uso personal). Si se va a compartir o distribuir públicamente, añade un fichero `LICENSE` acorde al uso previsto.
