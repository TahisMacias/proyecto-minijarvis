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
  **Su tabla de modelos (seccion 4) lleva un aviso de correccion**: los identificadores
  originales no los sirve esta cuenta. Antes de copiar cualquier dato de este documento
  al informe, contrastarlo con `config.py`.

## Important product paths

- `Proyecto_MiniJARVIS.pdf`: enunciado oficial. Requisitos y rubrica. Maxima autoridad
  academica; ante cualquier conflicto, manda este documento.
  **No esta versionado**: es documento del docente y el repositorio es publico.
  Vive solo en la carpeta local, excluido por `.gitignore`. Su contenido esta
  reflejado en `APPCORE.md` y en `docs/specs/2026-08-13-mini-jarvis-design.md`.
- `Sintesis del proyecto.md`: **DOCUMENTO SUPERADO**, marcado como tal el 2026-08-23.
  Es la sintesis previa a construir nada. Contradice cinco decisiones vigentes y lleva
  la tabla de contradicciones al principio. No citarlo en el informe.
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
- `core/modo_local.py` (T-21): respaldo sin internet. Oye, piensa y habla en local
  cuando se cae la red. Los envoltorios imitan la forma de las piezas de nube, por
  eso el orquestador no se entera. `python -m core.modo_local` descarga los modelos.
- `core/tts_engine.py` (T-08): texto -> voz reproducida. `python -m core.tts_engine`
  como comprobacion manual (H-07).
- `core/orchestrator.py` (T-09): maquina de estados y el hilo de cada turno. **No
  importa nada de la GUI**; una prueba lee su AST para que siga siendo cierto.
- `gui/desktop_app.py` (T-10, T-13, T-14, T-19): la ventana, el puente `after(0, ...)`
  entre hilos, los controles de sustentacion y la superposicion del mapa. Tema oscuro,
  tres columnas, **sin pestanas** desde el rediseno del 2026-08-23.
- `main.py`: punto de entrada. `Iniciar Mini-JARVIS.bat`: lanzador con doble clic.
- `tests/`: memoria, parseo del LLM, orquestador, paleta de estados, barra
  espaciadora y herramientas. **171 pruebas**, sin red, sin microfono y sin saldo.
- `pytest.ini`: `pythonpath = .` para que el comando del gate encuentre `core`.
- `requirements.txt`: 14 dependencias fijadas. Auditado con AST el 2026-08-23: los 11
  imports de terceros estan declarados. Tres pines (`psutil`, `duckduckgo-search`,
  `tiktoken`) estan reservados para tareas sin construir y marcados como tales.
- `README.md`: cara publica del proyecto. Su tabla de modelos **debe** coincidir con
  `config.py`; se desincronizo una vez y no lo detecto ningun gate.
- `tools/manifest.py` (T-15): lo que el modelo LEE para decidir que herramienta pedir.
  Texto que viaja a la API: nada sensible aqui.
- `tools/system_skills.py` (T-15): **la superficie de riesgo del proyecto.** Hace
  cuentas con texto de un modelo y abre un proceso. Dos reglas: **nada de `eval`**
  (analisis con `ast` y lista blanca) y la url se valida por hostname ANTES de
  construir el comando, que es una lista de argumentos y nunca una cadena.
- `tests/test_tools.py`: 78 pruebas. La mas importante lee el AST de `tools/` y falla
  si aparece `eval`, `exec` o `compile`. Verifica una prohibicion, no un comportamiento.

## Documentacion para personas

- `docs/informe-tecnico.md` (T-16): borrador del informe. Cifras verificadas contra el
  repositorio, no recordadas. Pendiente de que la duena lo lea (H-16).
- `docs/guion-video.md` (T-17): guion del video por bloques de tiempo, escrito para
  leerse mientras se graba. Incluye que recortar si sobra metraje y las tres frases
  minimas con las que el video ya cumple.
- `docs/guion-mapa-atencion.md`: como explicar el mapa de atencion, que es el 25 % de
  la rubrica. Escrito porque la duena miro el grafico y no lo entendia: correcto y sin
  explicar no vale como entregable.
- `docs/pruebas-manuales.md`: recorrido de pruebas de la Fase 1, escrito para usarse.
- `docs/evidencia/`: salida del laboratorio, captura de la ventana y la tabla de
  cobertura de los 7 fallos previstos.

Last reindexed: 2026-08-23, al cerrar la sesion del repaso al enunciado.
