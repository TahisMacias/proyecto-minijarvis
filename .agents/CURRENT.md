# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-14
source_commit: (ver ultimo [STATE]; limpio y sincronizado con origin/main)
assurance: Lean
active_plan: PLAN_v1.0-entrega-27ago.md
active_task: T-12 (ultima de la Fase 1)
last_verdict: T-04 a T-11 APTO (toda la Fase 1 salvo T-12)
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico)
deadline: 2026-08-27
```

## COMO RETOMAR EN UNA SESION NUEVA

Di "continua el plan". Todo el estado vive aqui, no en ninguna conversacion.
Orden de lectura: este archivo -> `PLAN_v1.0-entrega-27ago.md` -> `AGENTS.md`.
El diseno completo esta en `docs/specs/2026-08-13-mini-jarvis-design.md`.

### Estado al cerrar la sesion del 2026-08-14

1. **T-11 esta cerrada y APTO** (commit `f1a9f43`). El aviso de la sesion anterior
   ("T-11 no se hizo, el archivo no existe") era **falso**: el Obrero si entrego,
   pero su codigo entro por error dentro del commit de T-03 y nadie lo audito.
   Leccion de proceso: verificar `git show --stat` antes de declarar que una tarea
   no se hizo. Un archivo puede existir y aun asi no estar cerrado.
2. **Decision abierta sobre la jerarquia de tres niveles.** El Ingeniero se detuvo a
   mitad de su primera tanda sin emitir veredictos; hubo que reanudarlo. Criterio ya
   acordado con la duena: si vuelve a fallar, se elimina el nivel intermedio y el
   Arquitecto despacha Obreros declarando cada despacho en voz alta. Un incidente no
   es patron; dos si.

## Next action

1. **T-09, el orquestador.** Es la tarea de mayor riesgo tecnico del plan: hilo
   trabajador por turno, maquina de estados y la regla de que ningun hilo toca un
   widget. Todas sus dependencias estan cerradas.
2. Luego T-10 (GUI) y T-12 (cierre del nucleo). Con eso cierra la Fase 1.

## Blockers

- Ninguno. Los dos bloqueos de la sesion anterior se resolvieron el 2026-08-13.

## Current facts

- **Entrega: 27 de agosto de 2026.** 14 dias desde el inicio del proyecto.
- Diseno aprobado y versionado en `docs/specs/2026-08-13-mini-jarvis-design.md`.
- Plan activo de 18 tareas en 3 fases con fechas de corte: nucleo 22 ago,
  valor agregado 25 ago, cierre 27 ago.
- Repositorio publico en `https://github.com/TahisMacias/proyecto-minijarvis`,
  12 commits publicados, local y remoto sincronizados.
- `gh` CLI v2.97.0 autenticado como `TahisMacias`, scopes `repo` y `workflow`.
- `TOGETHER_API_KEY` en `.env` local, validada contra `GET /v1/models` (HTTP 200).
- **Modelos: los dos IDs del plan original NO los sirve esta cuenta.**
  `Qwen/Qwen2.5-72B-Instruct` y `meta-llama/Llama-3.3-70B-Instruct` aparecen en
  `GET /v1/models` pero al pedirles una respuesta devuelven HTTP 400 "Unable to
  access non-serverless model": estan en el catalogo, no en el servicio compartido.
  Aparecer en el listado no prueba disponibilidad; solo la prueba una peticion de
  chat real. Se probaron catorce identificadores uno por uno.
  IDs vigentes, ambos con respuesta real verificada (`config.py`, commit `38715f7`):
  predeterminado `meta-llama/Llama-3.3-70B-Instruct-Turbo`, alterno
  `Qwen/Qwen2.5-7B-Instruct-Turbo`. `openai/whisper-large-v3` si funciona: se
  transcribio audio real de extremo a extremo.
- El tokenizador de Llama 3.3 en Hugging Face es un repositorio restringido (exige
  aceptar la licencia de Meta). Por eso el nivel 1 del laboratorio usa el de Qwen2.5,
  que es publico y ademas es el del modelo alterno real del proyecto.
- El enunciado en PDF **no esta versionado** a proposito: es material del docente y
  el repositorio es publico. Vive en local, excluido por `.gitignore`.
- **Python 3.14.5 confirmado como interprete definitivo** (T-01). Todo el stack
  instala con wheels nativos `cp314`, `torch 2.13.0+cpu` incluido. Riesgo cerrado.
- Entorno virtual creado en `.venv/` con los 11 paquetes instalados.
- **T-11 entregado y APTO.** `exploration/transformer_lab.py` corre con exit 0 y
  genera `exploration/mapa_atencion.png` (capa 6, cabeza 4: cabeza de token
  anterior). La salida completa esta versionada en
  `docs/evidencia/T-11-salida-transformer_lab.txt` y sirve de material directo para
  el informe (T-16) y la sustentacion. El 25% mas pesado de la rubrica esta cubierto.
- La extraccion de self-attention sobre BETO requiere `attn_implementation="eager"`;
  el script lo verifica en tiempo de ejecucion y falla con mensaje explicito si no.
- Microfono verificado: 10 dispositivos, Realtek por defecto, captura real correcta.
- Esqueleto del repositorio completo: `README.md`, `requirements.txt` con 12
  versiones fijadas, `.env.example`, y los cuatro paquetes importables.
- `config.py` existe y esta APTO: carga segura de credenciales, paleta de 5 acentos,
  IDs de modelo, limites de memoria y lista blanca de dominios. Es la fuente unica
  de verdad de configuracion; ningun otro modulo debe leer variables de entorno.
- **El pipeline de voz funciona de extremo a extremo.** Verificado sin GUI con los
  modulos reales: audio -> Whisper -> Llama -> voz reproducida, con la secuencia de
  estados correcta y vuelta a REPOSO, en 21.8 s.
- **`core/` completo y APTO el 2026-08-14**: `memory.py` (T-04), `audio_capture.py`
  (T-05), `stt_client.py` (T-06), `llm_engine.py` (T-07), `tts_engine.py` (T-08) y
  `orchestrator.py` (T-09). Mas `gui/desktop_app.py` y `main.py` (T-10).
- El orquestador **no importa nada de la GUI**: su unico canal de salida es un
  callback que la ventana envuelve en `root.after(0, ...)`. Hay una prueba que analiza
  el AST y falla si aparece un import de tkinter, customtkinter o gui.
- La ventana calcula su altura contra la pantalla real y su escalado. Con el 133 % de
  esta maquina, la altura fija de 680 dejaba el boton debajo de la barra de tareas.
- Suite de pruebas: 59 verdes en ~3 s (`tests/test_memory.py`,
  `tests/test_llm_parsing.py`, `tests/test_orchestrator.py`,
  `tests/test_paleta_estados.py`). Se anadio `pytest==9.1.1` a `requirements.txt` y
  `pytest.ini` con `pythonpath = .`, sin lo cual el comando del gate no encuentra
  el paquete `core`.
- La reproduccion de voz usa **MCI** (interfaz multimedia de Windows) via `ctypes`:
  Windows decodifica el MP3 de edge-tts sin dependencias extra.
- Falta `tools/` (T-15, tool calling), que es Fase 2. El orquestador ya lo soporta:
  recibe `ejecutar_herramienta` y respeta el limite de 2 rondas; sin ese argumento
  responde con el texto disponible, que es lo que hace hoy.

## Open findings

- El nivel Ingeniero **si** aporto independencia real en T-03: corrio sus propios
  gates y probo un caso que nadie le pidio (variable en blanco `"   "`, tambien
  rechazada). Pero se detuvo dos veces esperando a sus Obreros. Veredicto pendiente
  de la segunda observacion; criterio escrito en la seccion de trabajo a medias.

- La sintesis original del equipo proponia `asyncio` y 7 herramientas. El diseno
  aprobado se aparta en ambos puntos, con motivos registrados en CONTEXT y en el spec.
  `Sintesis del proyecto.md` sigue en el repositorio como documento historico; si
  genera confusion mas adelante, conviene marcarlo como superado.

## Human actions

- [x] Autenticacion con GitHub. Verificado 2026-08-13.
- [x] `TOGETHER_API_KEY` en `.env`, validada contra la API. Verificado 2026-08-13.
- [x] Proveedor de STT decidido: `openai/whisper-large-v3`.
- [ ] **H-04**: escuchar la calidad del audio capturado -> `python -m core.audio_capture`.
- [ ] **H-07**: escuchar la naturalidad de la voz -> `python -m core.tts_engine`.
- [ ] Verificar saldo en Together AI la vispera de la sustentacion (26 ago).
- [ ] No reactivar OneDrive durante el proyecto.
- [ ] Reservar los dias 26 y 27 para informe, video y ensayo. Sin codigo.
