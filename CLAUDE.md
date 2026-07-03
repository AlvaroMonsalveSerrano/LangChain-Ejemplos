# CLAUDE.md

Este fichero proporciona orientación a Claude Code (claude.ai/code) cuando trabaja con el código de este repositorio.

## Configuración

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# No existe .env.example en el repo: crea un fichero .env en la raíz
# con las API keys reales (ver tabla de variables en README.md).
```

> En macOS x86_64, `pip install -r requirements.txt` puede fallar al compilar `cbor2` (dependencia transitiva de `modal`) por falta de compilador de Rust. Solución: `pip install "cbor2==5.7.1"` antes de instalar el resto.

## Comandos

```bash
# Ejecutar un módulo
python 00basico/01_basico_agentes.py

# Ejecutar todos los módulos de una carpeta en orden
for f in 00basico/0*.py; do python "$f"; done
for f in 01agentes/0*.py; do python "$f"; done
for f in 03mensajes/0*.py; do python "$f"; done
```

No hay tests implementados todavía (ver sección Tests en README.md).

## Arquitectura

Sandbox de pruebas conceptuales para LangChain. Cada fichero numerado dentro de una carpeta temática (p. ej. `00basico/`) es un script autocontenido que demuestra un concepto. Los módulos encapsulan su lógica en funciones (`build_*`, `main`) con guardia `if __name__ == "__main__": main()`, y loggean el resultado en vez de usar `print`.

**Patrón central actual**: creación de agentes con `create_agent` (LangChain) y `create_deep_agent` (`deepagents`), no composición LCEL con pipe.

| Fichero | Concepto |
|---------|----------|
| `00basico/01_basico_agentes.py` | Agente mínimo con `create_agent`, una tool simple (`get_weather`) y Claude Haiku. |
| `00basico/02_basico_agentes.py` | Compara `create_agent` vs `create_deep_agent` sobre la misma tarea (analizar *El gran Gatsby* vía una tool `fetch_text_from_url` con validación anti-SSRF), con checkpointer, manejo de errores en las invocaciones y logging estructurado. |
| `01agentes/01_agentes_core.py` | Agente con una tool y salida estructurada tipada vía `response_format` (Pydantic), leída de `result["structured_response"]`. |
| `01agentes/02_agentes_core_context.py` | Añade contexto de ejecución vía `context_schema` (datos de la petición, p. ej. `user_id`) y `thread_id` por ejecución con `uuid7()`. |
| `01agentes/03_agentes_streaming.py` | Sustituye `agent.invoke` por `agent.stream(..., stream_mode="values")` para procesar el estado del grafo paso a paso. |
| `01agentes/04_agentes_gestion_contexto.py` | Gestiona contexto con middleware de `deepagents` (`FilesystemMiddleware`, `SummarizationMiddleware`, `MemoryMiddleware`, `SkillsMiddleware`) sobre un `FilesystemBackend` en `01agentes/context/`. |
| `01agentes/05_agentes_planificacion_delegacion.py` | Añade planificación (`TodoListMiddleware`) y delegación en subagentes efímeros (`SubAgentMiddleware`) sobre un `StateBackend` compartido. |
| `03mensajes/01_mensajes.py` | Invoca un modelo de chat directamente (sin `create_agent`) con un historial de `SystemMessage`/`HumanMessage`/`AIMessage`; loggea `response.usage_metadata`. |
| `03mensajes/02_mensajes_herramientas.py` | Vincula una tool al modelo con `model.bind_tools([search])` (sin agente) e inspecciona `response.tool_calls` en vez de `response.text`, que llega vacío cuando el turno solo llama a una tool. |

Las carpetas `02modelos/` y `04herramientas/` existen pero están vacías, pendientes de desarrollo.

## Estilo de Python

+ Versión: Python 3.11+. Usa sintaxis moderna (match, X | Y en tipos, list[int] en vez de List[int]).
+ Formato: black (line length 88) + ruff para lint. Sin excepciones manuales de estilo.
+ Tipado: type hints obligatorios en toda función pública (params y return). mypy --strict debe pasar sin errores.
+ Nombres: snake_case para funciones/variables, PascalCase para clases, UPPER_SNAKE_CASE para constantes. Nombres descriptivos, sin abreviaturas crípticas.
+ Estructura de proyecto: código en src/<paquete>/, tests en tests/ reflejando la misma estructura. Un módulo, una responsabilidad.
+ Funciones: cortas y con una sola responsabilidad. Máximo ~40 líneas como guía; si crece, extraer.
+ Docstrings: estilo Google, solo en funciones/clases públicas no triviales. No documentar lo obvio.
+ Errores: excepciones específicas, nunca except: desnudo ni except Exception salvo en el borde de la app (ej. main loop). Mensajes de error accionables.
+ Imports: absolutos, agrupados y ordenados (stdlib / terceros / locales), gestionado por ruff --select I o isort.
+ Inmutabilidad por defecto: preferir dataclass(frozen=True) o NamedTuple cuando el objeto no necesita mutar.
+ Dependencias: gestión con uv o poetry; versiones fijadas en lockfile. Evitar añadir dependencias para tareas triviales.
+ Testing: pytest, un test por comportamiento, nombres descriptivos (test_<qué>_<condición>_<resultado esperado>). Cobertura mínima 80% en lógica de negocio.
+ Concurrencia/IO: asyncio para IO-bound; evitar mezclar código sync/async sin necesidad clara.
+ Logging: módulo logging estándar, nunca print en código de producción.
+ Comentarios: explican el por qué, no el qué (el código ya dice el qué).

## Convenciones

- Todos los módulos cargan las credenciales mediante `python-dotenv` (`load_dotenv()` al inicio), después de insertar la raíz del proyecto en `sys.path` (`sys.path.insert(0, str(Path(__file__).parent.parent))`) para poder importar `utils`.
- Los nuevos módulos deben seguir el esquema `NN_nombre_concepto.py` y ubicarse en la carpeta temática numerada correspondiente (`00basico/`, `01agentes/`, etc.).
- Logging homogéneo vía `utils/logger.py`: `logger = logging.getLogger("<nombre>")` seguido de `utils.logger.configure_logging(logger, "INFO")`.
- Modelo por defecto actual: `claude-haiku-4-5-20251001` (vía `model_provider="anthropic"`) para iterar con coste bajo; cambiar a un modelo más capaz solo cuando el concepto lo requiera.
- Los modelos Pydantic para salida estructurada se definen en el mismo fichero del módulo que los usa (no se necesita un módulo de modelos compartido a esta escala).
