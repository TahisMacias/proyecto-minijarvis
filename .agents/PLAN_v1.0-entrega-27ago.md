# PLAN v1.0 - Entrega 27 de agosto

Status: active
Goal: entregar Mini-JARVIS funcionando, con informe, video y sustentacion preparada,
antes del 2026-08-27.
Assurance: Lean
Diseno de referencia: `docs/specs/2026-08-13-mini-jarvis-design.md`

## Reglas de este plan

- **Las fechas de corte mandan sobre el alcance.** Si una fase llega a su fecha sin
  cerrar, se recorta la siguiente; no se mueve la entrega.
- La Fase 2 **no empieza** hasta que la Fase 1 este completa y verificada.
- La Fase 3 es intocable: del 26 al 27 no se escribe codigo de producto.
- Roles: el Obrero (Sonnet) implementa, el Ingeniero (Opus) audita cada tarea, el
  Arquitecto audita el cierre de fase y hace commit y push. Ver `AGENTS.md`.

---

# FASE 1 - NUCLEO (13 al 22 de agosto)

Protege el 65% de la rubrica. Al cerrar esta fase el proyecto ya cumple todos los
requisitos obligatorios de la seccion 5.1 del enunciado.

### T-01 - Decidir el interprete verificando el stack real

- Status: ready
- Depends on: none
- Tipo: spike. Su salida es una decision, no codigo que se conserve.
- Scope: `.agents/AGENTS.md`, `requirements.txt` (borrador)
- Acceptance:
  - [ ] Evidencia real de `pip install` para: `customtkinter`, `edge-tts`, `openai`,
        `sounddevice`, `tiktoken`, `transformers`, `torch`, `matplotlib`, `psutil`,
        `duckduckgo-search`, `python-dotenv`.
  - [ ] Decision escrita: seguir en 3.14.5 o fijar otra version.
  - [ ] La version elegida queda en `AGENTS.md` > Environment.
  - [ ] Se verifica que el microfono es accesible desde Python y que hay al menos un
        dispositivo de entrada.
- Gates: creacion del venv e instalacion; se registra el codigo de salida de cada paso.
- Human checks: H-01, H-02
- Risk triggers: si `torch` no instala, T-11 cambia de alcance.
- STOP when: haya que instalar un interprete nuevo en la maquina. Lo decide la duena.

### T-02 - Esqueleto del repositorio reproducible

- Status: blocked (T-01)
- Depends on: T-01
- Scope: `README.md`, `requirements.txt`, `.env.example`, `core/__init__.py`,
  `tools/__init__.py`, `gui/__init__.py`, `exploration/__init__.py`
- Acceptance:
  - [ ] `README.md` documenta requisitos, venv, instalacion y ejecucion, y el comando
        exacto del modulo de exploracion.
  - [ ] `requirements.txt` con versiones fijadas que instalan limpio.
  - [ ] `.env.example` lista `TOGETHER_API_KEY` sin ningun valor real.
  - [ ] `git status` no muestra `.env` ni `.venv/`.
- Gates: `python -m compileall .`
- Human checks: H-03
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-03 - Configuracion y credenciales

- Status: blocked (T-02)
- Depends on: T-02
- Scope: `config.py`
- Acceptance:
  - [ ] `TOGETHER_API_KEY` se lee de `.env` con `python-dotenv`. Ninguna clave literal.
  - [ ] Si falta la clave, mensaje claro y la app no arranca a medias.
  - [ ] Paleta pastel, IDs de modelo, voz TTS y limites de memoria centralizados aqui.
  - [ ] Lista blanca de dominios para `abrir_kiosk` definida aqui.
- Gates: `python -m compileall .`; `git grep` sin coincidencias de patrones de secreto.
- Human checks: none
- Risk triggers: **si** — manejo de credenciales. Auditoria del modelo obligatoria.
- STOP when: se detecte una clave ya commiteada. Escala al Arquitecto de inmediato.

### T-04 - Memoria conversacional

- Status: blocked (T-03)
- Depends on: T-03
- Scope: `core/memory.py`, `tests/test_memory.py`
- Es la pieza mas facil de verificar sin APIs. Se hace temprano a proposito.
- Acceptance:
  - [ ] Mantiene los ultimos 10 turnos; el system prompt nunca se descarta.
  - [ ] Al superar el limite descarta el par mas antiguo, no el mas nuevo.
  - [ ] Expone conteo de turnos y estimacion de tokens para el indicador de la GUI.
  - [ ] Tests cubren: vacia, por debajo del limite, justo en el limite, por encima.
- Gates: `pytest tests/test_memory.py`
- Human checks: none
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-05 - Captura de audio

- Status: blocked (T-03)
- Depends on: T-03
- Scope: `core/audio_capture.py`
- Acceptance:
  - [ ] Graba del microfono a `io.BytesIO`, sin archivo temporal en disco.
  - [ ] Empieza y para bajo control explicito (push-to-talk), no por temporizador.
  - [ ] Si no hay dispositivo de entrada, lanza un error tipado que la GUI sabe mostrar.
  - [ ] Formato de salida compatible con el endpoint de transcripcion.
- Gates: `python -m compileall .`
- Human checks: H-04
- Risk triggers: drivers de audio en Windows.
- STOP when: no se logre capturar audio tras agotar las opciones de `sounddevice`.

### T-06 - Cliente STT

- Status: blocked (T-05)
- Depends on: T-05
- Scope: `core/stt_client.py`
- Acceptance:
  - [ ] Envia los bytes a `openai/whisper-large-v3` con `language="es"`.
  - [ ] Devuelve texto limpio; transcripcion vacia es un caso de retorno, no excepcion.
  - [ ] Errores de red, timeout y 401 se traducen a errores tipados.
  - [ ] Ningun fragmento de la API key aparece en mensajes de error.
- Gates: `python -m compileall .`
- Human checks: H-05
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-07 - Motor LLM

- Status: blocked (T-04)
- Depends on: T-04
- Scope: `core/llm_engine.py`
- Acceptance:
  - [ ] Cliente `openai` con `base_url="https://api.together.xyz/v1"`.
  - [ ] System prompt documentado que define la personalidad y **declara ser una IA
        cuyas respuestas pueden contener errores** (seccion 11 del enunciado).
  - [ ] `temperature` y `top_p` son parametros, no constantes: los sliders los leeran.
  - [ ] El modelo se puede cambiar entre Qwen y Llama sin reiniciar.
  - [ ] Devuelve texto o peticion de tool; el motor no ejecuta herramientas.
- Gates: `pytest tests/test_llm_parsing.py` (parseo de respuestas, con datos fijos)
- Human checks: H-06
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-08 - Motor TTS

- Status: blocked (T-03)
- Depends on: T-03
- Scope: `core/tts_engine.py`
- Acceptance:
  - [ ] `edge-tts` con voz `es-MX-DaliaNeural`, invocado con `asyncio.run()` local.
  - [ ] Reproduce el audio y devuelve el control al terminar.
  - [ ] Si `edge-tts` falla, se propaga un error tipado sin romper el flujo.
- Gates: `python -m compileall .`
- Human checks: H-07
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-09 - Orquestador y maquina de estados

- Status: blocked (T-06, T-07, T-08)
- Depends on: T-06, T-07, T-08
- **Es la tarea de mayor riesgo tecnico del plan.**
- Scope: `core/orchestrator.py`
- Acceptance:
  - [ ] Estados ESCUCHANDO, PENSANDO, RESPONDIENDO, ATENCION, REPOSO. De ATENCION
        siempre se vuelve a REPOSO.
  - [ ] Un hilo trabajador efimero por turno. Sin bucle `asyncio` persistente.
  - [ ] **Ningun hilo trabajador toca un widget.** El unico canal de retorno hacia la
        GUI es un callback que la GUI despacha con `root.after`.
  - [ ] Ninguna excepcion sube hasta el `mainloop`.
  - [ ] Maximo 2 rondas de tool calling; al agotarse responde con el texto disponible.
- Gates: `pytest tests/test_orchestrator.py` con dobles de STT, LLM y TTS.
- Human checks: H-08
- Risk triggers: **si** — concurrencia. Auditoria del modelo obligatoria.
- STOP when: la GUI se congele y la causa no sea evidente en una sesion de trabajo.

### T-10 - Interfaz de escritorio

- Status: blocked (T-09)
- Depends on: T-09
- Scope: `gui/desktop_app.py`, `main.py`
- Acceptance:
  - [ ] Ventana CustomTkinter en modo claro con la paleta pastel de `config.py`.
  - [ ] Los 4 estados son distinguibles a simple vista, sin leer texto.
  - [ ] Boton push-to-talk funcional; la barra espaciadora hace lo mismo.
  - [ ] Panel de conversacion con el historial visible.
  - [ ] Los errores aparecen como mensajes amables, sin trazas tecnicas.
  - [ ] `python main.py` levanta la aplicacion.
- Gates: `python -m compileall .`
- Human checks: H-09, H-10
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-11 - Modulo de exploracion del Transformer

- Status: blocked (T-01)
- Depends on: T-01
- **Criterio de mayor peso de la rubrica (25%). No se recorta bajo ninguna circunstancia.**
- Scope: `exploration/transformer_lab.py`
- Acceptance:
  - [ ] Nivel 1: tokenizador real de `Qwen/Qwen2.5-72B-Instruct` (sin pesos). Imprime
        tokens e IDs de una frase en espanol del propio proyecto.
  - [ ] Nivel 2: `dccuchile/bert-base-spanish-wwm-cased` con `output_attentions=True`.
        Imprime la forma del tensor de embeddings y explica que significa cada dimension.
  - [ ] Genera un mapa de calor PNG de una capa y cabeza concretas, con los tokens
        etiquetados en ambos ejes.
  - [ ] Corre solo, sin la GUI, con el comando documentado en el README.
  - [ ] Cada seccion tiene un comentario que explica el concepto, no solo el codigo.
- Gates: ejecucion del script; se conserva la salida y el PNG como evidencia.
- Human checks: H-11
- Risk triggers: **si** — depende de `torch`. Si T-01 lo descarto, el nivel 2 cambia
  de alcance y eso **para y sube al Arquitecto**.
- STOP when: `torch` no sea instalable en el interprete elegido.

### T-12 - Cierre del nucleo: errores y README

- Status: blocked (T-10, T-11)
- Depends on: T-10, T-11
- Scope: `README.md`, retoques de manejo de errores donde falte
- Acceptance:
  - [ ] Los 7 fallos de la seccion 13 del diseno estan cubiertos con mensaje propio.
  - [ ] Desconectar la red a mitad de un turno no rompe la aplicacion.
  - [ ] README permite instalar y ejecutar desde cero sin pasos no documentados.
- Gates: suite completa de `pytest`; `python -m compileall .`
- Human checks: H-12
- Risk triggers: ninguno
- STOP when: ninguna prevista.

## Cierre de Fase 1 — fecha limite 22 de agosto

- [ ] T-01 a T-12 en APTO.
- [ ] Checks humanos H-01 a H-12 completos.
- [ ] El pipeline completo funciona de extremo a extremo con voz real.
- [ ] Auditoria de fase del Arquitecto; commit y push.
- [ ] **Decision explicita**: si esta fase no cerro el 22, se recorta la Fase 2.

---

# FASE 2 - VALOR AGREGADO (23 al 25 de agosto)

Solo empieza si la Fase 1 cerro. En este orden estricto: lo que no entre, se descarta.

### T-13 - Pestana Laboratorio en la GUI

- Status: blocked (Fase 1)
- Depends on: T-11, T-10
- Scope: `gui/desktop_app.py`
- Acceptance:
  - [ ] Pestana que muestra tokens e IDs de la ultima frase transcrita.
  - [ ] Muestra el mapa de calor de atencion de esa frase.
  - [ ] Reutiliza la logica de `exploration/`; no la duplica.
  - [ ] Si el calculo tarda, no congela la ventana.
- Gates: `python -m compileall .`
- Human checks: H-13
- Risk triggers: ninguno
- STOP when: el calculo bloquee la GUI y no se resuelva en medio dia.

### T-14 - Controles de sustentacion

- Status: blocked (T-13)
- Depends on: T-10
- Scope: `gui/desktop_app.py`
- Acceptance:
  - [ ] Sliders de `temperature` y `top_p` que afectan la siguiente respuesta.
  - [ ] Indicador de turnos y tokens en memoria; marca visualmente el descarte.
  - [ ] Visor de solo lectura del system prompt.
  - [ ] Selector Qwen / Llama que cambia de modelo sin reiniciar.
- Gates: `python -m compileall .`
- Human checks: H-14
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-15 - Tool calling

- Status: blocked (T-14)
- Depends on: T-07, T-09
- Scope: `tools/manifest.py`, `tools/system_skills.py`, `tests/test_tools.py`
- Acceptance:
  - [ ] `estado_laptop` con `psutil`: bateria, RAM y CPU en tono conversacional.
  - [ ] `buscar_web` con `duckduckgo-search`.
  - [ ] `abrir_kiosk`: **valida la URL contra la lista blanca antes** de construir el
        comando, y arma el comando como lista de argumentos, nunca concatenando cadenas.
  - [ ] Los esquemas JSON del manifest son validos y el LLM los invoca correctamente.
  - [ ] Tests de las tres; de `abrir_kiosk` se verifica la lista blanca y la
        construccion del comando **sin lanzar el proceso**.
- Gates: `pytest tests/test_tools.py`
- Human checks: H-15
- Risk triggers: **si** — `abrir_kiosk` ejecuta un proceso. Auditoria obligatoria.
- STOP when: se proponga ejecutar cualquier comando fuera de la lista blanca.

## Cierre de Fase 2 — fecha limite 25 de agosto

- [ ] Las tareas que alcanzaron a hacerse estan en APTO.
- [ ] Lo no completado se documenta como trabajo diferido, sin dejarlo a medias.
- [ ] Nada queda a medio implementar en el repositorio.
- [ ] Auditoria de fase; commit y push.

---

# FASE 3 - CIERRE (26 y 27 de agosto)

**No se escribe codigo de producto en esta fase.**

### T-16 - Informe tecnico

- Status: blocked (Fase 2)
- Depends on: cierre de Fase 2
- Scope: `docs/informe-tecnico.md`
- Base: `docs/specs/2026-08-13-mini-jarvis-design.md` ya contiene arquitectura,
  decisiones, limitaciones y riesgos redactados.
- Acceptance:
  - [ ] 4 a 8 paginas.
  - [ ] Arquitectura del sistema con diagrama.
  - [ ] Fundamentacion teorica del Transformer apoyada en la salida real de `exploration/`.
  - [ ] Decisiones de diseno con su alternativa descartada.
  - [ ] Limitaciones conocidas, incluida la de inspeccionar atencion via API.
  - [ ] Cita explicita de modelos y proveedores usados.
- Gates: none
- Human checks: H-16
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-17 - Video demostrativo

- Status: blocked (T-16)
- Depends on: cierre de Fase 2
- Scope: archivo de video, fuera del repositorio
- Acceptance:
  - [ ] 2 a 4 minutos.
  - [ ] Muestra el pipeline completo con voz real y los estados de la interfaz.
  - [ ] Muestra el modulo de exploracion.
  - [ ] **Sirve de respaldo si la demo en vivo falla.**
- Gates: none
- Human checks: H-17
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-18 - Ensayo y verificacion final

- Status: blocked (T-17)
- Depends on: T-16, T-17
- Scope: `.agents/`, verificacion del repositorio
- Acceptance:
  - [ ] Las 6 preguntas guia de la seccion 12 del enunciado ensayadas en voz alta.
  - [ ] Saldo de Together AI verificado.
  - [ ] Repositorio publico revisado: sin credenciales, README correcto, historial
        progresivo visible.
  - [ ] Prueba de instalacion desde cero en otra maquina.
- Gates: barrido de secretos sobre todo el historial.
- Human checks: H-18
- Risk triggers: **si** — verificacion previa a entrega.
- STOP when: aparezca cualquier credencial en el repositorio publico.

## Closure gate del proyecto

- [ ] Todas las tareas ejecutadas en APTO.
- [ ] Checks humanos completos.
- [ ] Coherencia entre README, `requirements.txt`, `AGENTS.md` y la maquina real.
- [ ] CURRENT, INDEX, APPCORE, TESTING y Git concuerdan.
- [ ] Informe, video y repositorio entregados antes del 27 de agosto.
