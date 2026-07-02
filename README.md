# Ejem1-LangChain

Sandbox de pruebas conceptuales con la librería [LangChain](https://python.langchain.com/) (agentes, `deepagents`, modelos, mensajería y herramientas). Cada módulo es un script autocontenido que demuestra un concepto concreto del ecosistema.

---

## Estructura del proyecto

```
.
├── 00basico/          # Módulos desarrollados: creación de agentes
├── 01agentes/         # Pendiente de desarrollo
├── 02modelos/         # Pendiente de desarrollo
├── 03mensajes/        # Pendiente de desarrollo
├── 04herramientas/    # Pendiente de desarrollo
├── utils/
│   └── logger.py      # Configuración de logging compartida entre módulos
├── requirements.txt
└── CLAUDE.md           # Orientación específica para Claude Code
```

Cada carpeta numerada agrupa módulos de un mismo tema. Solo `00basico/` tiene módulos implementados por ahora (ver [Módulos desarrollados](#módulos-desarrollados)); el resto son carpetas reservadas para próximos ejemplos.

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
| `ANTHROPIC_API_KEY` | `00basico/01_basico_agentes.py`, `00basico/02_basico_agentes.py` | Credencial de Anthropic; los agentes actuales usan Claude Haiku. |
| `OPENAI_API_KEY` | Declarada como dependencia (`langchain-openai`) pero ningún módulo actual la usa todavía. | Necesaria si un módulo futuro usa modelos de OpenAI. |
| `TAVILY_API_KEY` | Declarada como dependencia (`tavily-python`) pero ningún módulo actual la usa todavía. | Necesaria si un módulo futuro añade búsqueda web con Tavily. |
| `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`, `LANGSMITH_PROJECT` | Opcional, vía `utils/logger.py` | Activan trazas remotas en LangSmith cuando se configuran; si se omiten, el logging queda solo en local (stdout). |

---

## Módulos desarrollados

| Módulo | Descripción |
|--------|-------------|
| [`00basico/01_basico_agentes.py`](00basico/01_basico_agentes.py) | Ejemplo mínimo de agente con `create_agent` de LangChain. Define una tool simple (`get_weather`), usa Claude Haiku como modelo y registra trazas con `utils/logger.py`. |
| [`00basico/02_basico_agentes.py`](00basico/02_basico_agentes.py) | Compara un agente estándar (`create_agent`) frente a un deep agent (`create_deep_agent` de `deepagents`) sobre la misma tarea: analizar el texto completo de *El gran Gatsby* descargado desde Project Gutenberg mediante la tool `fetch_text_from_url`. Incluye: checkpointer en memoria compartido entre ambos agentes (con `thread_id` distinto por agente), validación anti-SSRF en la tool de descarga (solo esquemas `http`/`https` y bloqueo de IPs privadas, loopback y link-local), manejo de errores en las invocaciones para que el fallo de un agente no impida ejecutar el otro, y logging estructurado con `utils/logger.py`. |

---

## Convenciones observadas en los módulos actuales

- Nomenclatura `NN_nombre_concepto.py` dentro de una carpeta temática numerada (p. ej. `00basico/`).
- Cada módulo añade la raíz del proyecto a `sys.path` (`sys.path.insert(0, str(Path(__file__).parent.parent))`) **antes** de importar `utils`, y carga credenciales con `python-dotenv` (`load_dotenv()`).
- Logging homogéneo vía `utils/logger.py`: `logger = logging.getLogger("<nombre>")` seguido de `utils.logger.configure_logging(logger, "INFO")`.
- La lógica se encapsula en funciones (`build_*`, `main`) con guardia `if __name__ == "__main__": main()`, en vez de código suelto a nivel de módulo.

> `CLAUDE.md` documenta además unas convenciones de plantilla (carpeta `examples/`, modelo por defecto `gpt-4o-mini`) que no coinciden con la práctica actual de `00basico/` — considéralo si retomas ese fichero.

---

## Cómo ejecutar los módulos

```bash
# Activar el entorno virtual si no está activo
source .venv/bin/activate

# Ejecutar un módulo concreto
python 00basico/01_basico_agentes.py

# Ejecutar todos los módulos de 00basico/ en orden
for f in 00basico/0*.py; do echo "=== $f ==="; python "$f"; done
```

> Todos los módulos imprimen (o loggean) su resultado por stdout. Asegúrate de que `.env` está configurado antes de ejecutarlos.

---

## Tests

🚧 **Pendiente:** todavía no hay ningún test implementado ni carpeta `tests/` en el repo.

El patrón previsto (documentado en `CLAUDE.md`) es usar `pytest` con un LLM simulado (`FakeListLLM`) para no depender de llamadas reales a la API ni de credenciales, con ficheros en `tests/` siguiendo la convención `test_<nombre_del_módulo>.py`.

---

## Estado del proyecto

- ✅ `00basico/` — 2 módulos de agentes implementados y verificados.
- 🚧 `01agentes/`, `02modelos/`, `03mensajes/`, `04herramientas/` — carpetas creadas, sin contenido todavía.
- 🚧 `tests/` — sin implementar.

---

## Licencia

Este repositorio no tiene una licencia definida todavía (sandbox de uso personal). Si se va a compartir o distribuir públicamente, añade un fichero `LICENSE` acorde al uso previsto.
