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

# Ejecutar todos los módulos de 00basico/ en orden
for f in 00basico/0*.py; do python "$f"; done
```

No hay tests implementados todavía (ver sección Tests en README.md).

## Arquitectura

Sandbox de pruebas conceptuales para LangChain. Cada fichero numerado dentro de una carpeta temática (p. ej. `00basico/`) es un script autocontenido que demuestra un concepto. Los módulos encapsulan su lógica en funciones (`build_*`, `main`) con guardia `if __name__ == "__main__": main()`, y loggean el resultado en vez de usar `print`.

**Patrón central actual**: creación de agentes con `create_agent` (LangChain) y `create_deep_agent` (`deepagents`), no composición LCEL con pipe.

| Fichero | Concepto |
|---------|----------|
| `00basico/01_basico_agentes.py` | Agente mínimo con `create_agent`, una tool simple (`get_weather`) y Claude Haiku. |
| `00basico/02_basico_agentes.py` | Compara `create_agent` vs `create_deep_agent` sobre la misma tarea (analizar *El gran Gatsby* vía una tool `fetch_text_from_url` con validación anti-SSRF), con checkpointer, manejo de errores en las invocaciones y logging estructurado. |

Las carpetas `01agentes/`, `02modelos/`, `03mensajes/` y `04herramientas/` existen pero están vacías, pendientes de desarrollo.

## Convenciones

- Todos los módulos cargan las credenciales mediante `python-dotenv` (`load_dotenv()` al inicio), después de insertar la raíz del proyecto en `sys.path` (`sys.path.insert(0, str(Path(__file__).parent.parent))`) para poder importar `utils`.
- Los nuevos módulos deben seguir el esquema `NN_nombre_concepto.py` y ubicarse en la carpeta temática numerada correspondiente (`00basico/`, `01agentes/`, etc.).
- Logging homogéneo vía `utils/logger.py`: `logger = logging.getLogger("<nombre>")` seguido de `utils.logger.configure_logging(logger, "INFO")`.
- Modelo por defecto actual: `claude-haiku-4-5-20251001` (vía `model_provider="anthropic"`) para iterar con coste bajo; cambiar a un modelo más capaz solo cuando el concepto lo requiera.
- Los modelos Pydantic para salida estructurada se definen en el mismo fichero del módulo que los usa (no se necesita un módulo de modelos compartido a esta escala).
