# INDEX - `.agents/`

- `AGENTS.md`: roles, assurance, limites, gates y reglas duraderas.
- `APPCORE.md`: hechos estables de producto y arquitectura objetivo.
- `CURRENT.md`: estado activo, bloqueos y siguiente accion.
- `CONTEXT.md`: decisiones y handoffs en orden cronologico.
- `PLAN_v1.0-entrega-27ago.md`: plan activo. 18 tareas en 3 fases con fechas de corte.
- `TESTING.md`: checks humanos H-01 a H-18 mas la regresion R-01.
- `archive/PLAN_v0.1-fundamentos.md`: superseded, nunca ejecutado. Se escribio antes
  de conocer la fecha de entrega.
- `archive/CONTEXT_2026-08-13.md`: texto completo de las seis entradas de la primera
  jornada. Se compactaron en `CONTEXT.md` el 2026-08-14; esto es la fuente si hace
  falta el detalle.

## Diseno

- `docs/specs/2026-08-13-mini-jarvis-design.md`: documento de diseno aprobado.
  17 secciones. Es la referencia de toda tarea del plan y la base del informe tecnico.

## Important product paths

- `Proyecto_MiniJARVIS.pdf`: enunciado oficial. Requisitos y rubrica. Maxima autoridad
  academica; ante cualquier conflicto, manda este documento.
  **No esta versionado**: es documento del docente y el repositorio es publico.
  Vive solo en la carpeta local, excluido por `.gitignore`. Su contenido esta
  reflejado en `APPCORE.md` y en `docs/specs/2026-08-13-mini-jarvis-design.md`.
- `Sintesis del proyecto.md`: decisiones de diseno del equipo — stack, paleta,
  catalogo de herramientas y estructura modular objetivo.
- `.gitignore`: primera linea de defensa contra publicar credenciales.
- `.claude/skills/agents-workflow/SKILL.md`: la skill que gobierna este workflow.

## Codigo de producto

- `config.py` (T-03): fuente unica de verdad de configuracion. Credenciales, paleta,
  IDs de modelo, limites de memoria y lista blanca de dominios. **Ningun otro modulo
  debe leer variables de entorno.**
- `exploration/transformer_lab.py` (T-11): laboratorio del Transformer. Independiente
  del resto del proyecto: no importa `config.py` ni nada de `core/`. Se ejecuta con
  `python -m exploration.transformer_lab`.
- `exploration/mapa_atencion.png`: salida del laboratorio, material de sustentacion.
- `docs/evidencia/T-11-salida-transformer_lab.txt`: salida de consola conservada como
  evidencia del gate de T-11 y como material para el informe tecnico (T-16).
- `core/memory.py` (T-04): historial y truncado por turnos. **No importa `config.py`**;
  recibe `system_prompt` y `max_turnos` como argumentos obligatorios.
- `core/audio_capture.py` (T-05): microfono -> WAV en `io.BytesIO`, push-to-talk.
  `python -m core.audio_capture` graba 3 s como comprobacion manual (H-04).
- `core/stt_client.py` (T-06): WAV -> texto con Whisper en Together AI.
- `core/llm_engine.py` (T-07): mensajes -> texto o peticion de tool. **No ejecuta
  herramientas.** Contiene el `SYSTEM_PROMPT` con la declaracion de ser una IA.
- `core/tts_engine.py` (T-08): texto -> voz reproducida. `python -m core.tts_engine`
  como comprobacion manual (H-07).
- `core/orchestrator.py` (T-09): maquina de estados y el hilo de cada turno. **No
  importa nada de la GUI**; una prueba lee su AST para que siga siendo cierto.
- `gui/desktop_app.py` (T-10, T-13): la ventana, el puente `after(0, ...)` entre hilos
  y la pestana Laboratorio.
- `main.py`: punto de entrada. `Iniciar Mini-JARVIS.bat`: lanzador con doble clic.
- `tests/`: memoria, parseo del LLM, orquestador, paleta de estados y barra
  espaciadora. 70 pruebas, sin red, sin microfono y sin saldo.
- `pytest.ini`: `pythonpath = .` para que el comando del gate encuentre `core`.
- Falta `tools/` (T-15, Fase 2 sin abrir).

## Documentacion para personas

- `docs/pruebas-manuales.md`: recorrido de pruebas de la Fase 1, escrito para usarse.
- `docs/evidencia/`: salida del laboratorio, captura de la ventana y la tabla de
  cobertura de los 7 fallos previstos.

Last reindexed: 2026-08-14, al cerrar la sesion de la Fase 1.
