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

- Status: **done** (2026-08-13). Ejecutada por el Arquitecto: es un spike de
  diagnostico cuya salida es una decision, no codigo.
- Depends on: none
- Scope: `.agents/AGENTS.md`
- Acceptance:
  - [x] Evidencia real de `pip install` para los 11 paquetes del stack. Exit code 0.
  - [x] Decision escrita: **se mantiene Python 3.14.5**. Riesgo cerrado.
  - [x] Versiones verificadas registradas en `AGENTS.md` > Environment.
  - [x] Microfono accesible: 10 dispositivos de entrada, captura real de 0.5s correcta.
  - [x] Caso de uso de T-11 verificado de extremo a extremo, no solo la instalacion.
- Resultado:
  - Todo el stack instala con wheels nativos `cp314`. `torch 2.13.0+cpu` incluido.
    **No hace falta bajar de version de Python.**
  - `openai 3.0.0` construye el cliente contra `https://api.together.xyz/v1`.
  - `edge-tts` expone `es-MX-DaliaNeural` entre 45 voces `es-*`.
  - BETO devuelve embeddings `(1, 20, 768)`, 12 capas de atencion de
    `(1, 12, 20, 20)`, y cada fila suma 1.0. Heatmap PNG generado.
  - **Hallazgo critico:** `transformers 5.x` usa SDPA por defecto y devuelve `None`
    en `output_attentions=True` sin lanzar error. Hay que cargar con
    `attn_implementation="eager"`. Registrado en Learned safeguards.
- Nota de alcance: `requirements.txt` se movio a T-02. Motivo: el Arquitecto no edita
  el product plane. Las versiones verificadas quedan en `AGENTS.md` como fuente de
  verdad para que el Obrero las fije.
- Human checks: H-01 [OK], H-02 [OK]

### T-02 - Esqueleto del repositorio reproducible

- Status: **done** (2026-08-13). Implementada por el Obrero, auditada por el
  Arquitecto. **Excepcion declarada**: se salto el nivel Ingeniero porque la tarea ya
  estaba en vuelo cuando se activo ese nivel. Desde T-03 el Ingeniero orquesta y audita.
- Veredicto: **APTO**. Gates verificados de forma independiente, no por reporte:
  7 archivos exactos sin desbordar alcance; `compileall` exit 0; `.env` y `.venv`
  invisibles para Git; los 4 paquetes importan.
- Aportes del Obrero fuera del brief, aceptados:
  - Paso de `Set-ExecutionPolicy` en el README. Sin el, `Activate.ps1` falla bajo la
    politica por defecto de Windows y el README no seria reproducible en otra maquina,
    que era el objetivo de la tarea.
  - Reporto que `.env` contiene una clave real, verificando que no esta en el
    historial y **sin reproducir el valor**. Comportamiento correcto.
- Depends on: T-01 (cerrada)
- Scope: `README.md`, `requirements.txt`, `.env.example`, `core/__init__.py`,
  `tools/__init__.py`, `gui/__init__.py`, `exploration/__init__.py`
- Acceptance:
  - [x] `README.md` documenta requisitos, venv, instalacion y ejecucion, y el comando
        exacto del modulo de exploracion. Debe indicar **Python 3.14.5**.
  - [x] `requirements.txt` fija exactamente las 12 versiones de la tabla de
        `AGENTS.md` > Environment. Ni mas recientes ni sin fijar.
  - [x] `.env.example` lista `TOGETHER_API_KEY` sin ningun valor real.
  - [x] `git status` no muestra `.env` ni `.venv/`.
- Gates: `python -m compileall .`
- Human checks: H-03
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-03 - Configuracion y credenciales

- Status: **done** (2026-08-13). Veredicto: **APTO** (commit `6d0cf88`).
  Auditada por el Ingeniero con gates propios y releida por el Arquitecto antes de
  publicar a un repositorio publico. Incluye la correccion de paleta (ATENCION pasa
  a durazno `#FFF3E0`), aplicada por el Arquitecto como excepcion declarada.
- Depends on: T-02 (cerrada)
- Despacho: **Ingeniero** (tiene `Risk triggers: si`)
- Scope: `config.py`
- Acceptance:
  - [x] `TOGETHER_API_KEY` se lee de `.env` con `python-dotenv`. Ninguna clave literal.
  - [x] Si falta la clave, mensaje claro y la app no arranca a medias.
  - [x] Paleta pastel, IDs de modelo, voz TTS y limites de memoria centralizados aqui.
  - [x] Lista blanca de dominios para `abrir_kiosk` definida aqui.
- Gates: `python -m compileall .`; `git grep` sin coincidencias de patrones de secreto.
- Human checks: none
- Risk triggers: **si** — manejo de credenciales. Auditoria del modelo obligatoria.
- STOP when: se detecte una clave ya commiteada. Escala al Arquitecto de inmediato.

### T-04 - Memoria conversacional

- Status: **done** (2026-08-14). Veredicto: **APTO** (commit `04f2fbc`).
  Gate ejecutado: 13 pruebas verdes con `pytest tests/test_memory.py`.
  Desviacion declarada y justificada: el modulo **no importa `config.py`**. La tabla
  de modulos del diseno lo lista sin dependencias; `system_prompt` y `max_turnos` son
  argumentos obligatorios, asi no se duplica ninguna constante y las pruebas corren
  en una maquina sin `.env`. El orquestador (T-09) pasara `MAX_TURNOS_MEMORIA`.
  Se anadio `pytest==9.1.1` a `requirements.txt` y `pytest.ini` con `pythonpath = .`;
  sin eso el comando del gate falla con `No module named 'core'`.
- Depends on: T-03
- Scope: `core/memory.py`, `tests/test_memory.py`
- Es la pieza mas facil de verificar sin APIs. Se hace temprano a proposito.
- Acceptance:
  - [x] Mantiene los ultimos 10 turnos; el system prompt nunca se descarta.
  - [x] Al superar el limite descarta el par mas antiguo, no el mas nuevo.
  - [x] Expone conteo de turnos y estimacion de tokens para el indicador de la GUI.
  - [x] Tests cubren: vacia, por debajo del limite, justo en el limite, por encima.
- Gates: `pytest tests/test_memory.py`
- Human checks: none
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-05 - Captura de audio

- Status: **done** (2026-08-14). Veredicto: **APTO** (commit `f7230a7`).
  Verificado sobre el microfono real: 3 s -> 88 236 bytes, cabecera RIFF/WAVE valida,
  el WAV se relee con el modulo `wave` y da 1 canal, 16 bits, 16 kHz. Los tres errores
  tipados se provocaron a proposito y salieron correctos. `compileall` exit 0.
  Pendiente **H-04** (calidad del audio a oido de la duena):
  `python -m core.audio_capture` graba 3 s y reporta.
- Depends on: T-03
- Scope: `core/audio_capture.py`
- Acceptance:
  - [x] Graba del microfono a `io.BytesIO`, sin archivo temporal en disco.
  - [x] Empieza y para bajo control explicito (push-to-talk), no por temporizador.
  - [x] Si no hay dispositivo de entrada, lanza un error tipado que la GUI sabe mostrar.
  - [x] Formato de salida compatible con el endpoint de transcripcion: WAV PCM 16 bits,
        mono, 16 kHz, el nativo de Whisper.
- Gates: `python -m compileall .`
- Human checks: H-04
- Risk triggers: drivers de audio en Windows.
- STOP when: no se logre capturar audio tras agotar las opciones de `sounddevice`.

### T-06 - Cliente STT

- Status: **done** (2026-08-14). Veredicto: **APTO** (commit `5874a35`).
  Verificado contra la API real: se sintetizo una frase conocida con edge-tts y
  Whisper la devolvio transcrita. Los seis caminos de error se provocaron con
  clientes falsos y cada uno dio su tipo esperado; una excepcion que contenia la
  clave salio con la clave reemplazada por `***`.
- Depends on: T-05
- Scope: `core/stt_client.py`
- Acceptance:
  - [x] Envia los bytes a `openai/whisper-large-v3` con `language="es"`.
  - [x] Devuelve texto limpio; transcripcion vacia es un caso de retorno, no excepcion.
  - [x] Errores de red, timeout y 401 se traducen a errores tipados.
  - [x] Ningun fragmento de la API key aparece en mensajes de error.
- Gates: `python -m compileall .`
- Human checks: H-05
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-07 - Motor LLM

- Status: **done** (2026-08-14). Veredicto: **APTO** (commit `b620ac7`).
  Gate: 15 pruebas de parseo con datos fijos, sin red ni saldo. Verificacion
  adicional contra la API real: identidad declarada, cambio de modelo en caliente
  con la memoria viva (el segundo modelo recordo la pregunta hecha al primero) y una
  peticion de `tool_call` devuelta **sin ejecutar**, con su id y su mensaje crudo.
- **Hallazgo mayor de esta tarea** (ver T-03, commit `38715f7`): los dos IDs de
  modelo del plan no los sirve esta cuenta. Ver `CURRENT.md` > Current facts.
- Depends on: T-04
- Scope: `core/llm_engine.py`
- Acceptance:
  - [x] Cliente `openai` con `base_url="https://api.together.xyz/v1"`.
  - [x] System prompt documentado que define la personalidad y **declara ser una IA
        cuyas respuestas pueden contener errores** (seccion 11 del enunciado).
  - [x] `temperature` y `top_p` son parametros, no constantes: los sliders los leeran.
  - [x] El modelo se puede cambiar entre Qwen y Llama sin reiniciar. Verificado en
        caliente, con la conversacion viva.
  - [x] Devuelve texto o peticion de tool; el motor no ejecuta herramientas.
- Gates: `pytest tests/test_llm_parsing.py` (parseo de respuestas, con datos fijos)
- Human checks: H-06
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-08 - Motor TTS

- Status: **done** (2026-08-14). Veredicto: **APTO** (commit `ba169e1`).
  Verificado de extremo a extremo: MP3 real de 49 104 bytes sintetizado y reproducido;
  `reproducir()` tardo 4.92 s en una frase de esa duracion, o sea bloquea de verdad;
  texto vacio/en blanco/None -> `SintesisFallida`; sin temporales huerfanos.
  Decision de implementacion: la reproduccion usa **MCI** (interfaz multimedia de
  Windows) via `ctypes`. Windows decodifica el MP3 de edge-tts sin dependencias
  extra; anadir una libreria de audio solo para sonar no se justificaba.
  Pendiente **H-07** (naturalidad de la voz): `python -m core.tts_engine`.
- Depends on: T-03
- Scope: `core/tts_engine.py`
- Acceptance:
  - [x] `edge-tts` con voz `es-MX-DaliaNeural`, invocado con `asyncio.run()` local.
  - [x] Reproduce el audio y devuelve el control al terminar (medido: 4.92 s).
  - [x] Si `edge-tts` falla, se propaga un error tipado sin romper el flujo.
- Gates: `python -m compileall .`
- Human checks: H-07
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-09 - Orquestador y maquina de estados

- Status: **done** (2026-08-14). Veredicto: **APTO** (commit `c351170`).
  Gate: 24 pruebas con dobles. Verificacion adicional con los modulos reales, sin
  GUI: audio -> Whisper -> Llama -> voz, estados correctos, vuelta a REPOSO en 21.8 s.
  Defecto real encontrado por las pruebas: una transcripcion de puros espacios pasaba
  como texto valido. Corregido en el orquestador.
- Depends on: T-06, T-07, T-08
- **Es la tarea de mayor riesgo tecnico del plan.**
- Scope: `core/orchestrator.py`
- Acceptance:
  - [x] Estados ESCUCHANDO, PENSANDO, RESPONDIENDO, ATENCION, REPOSO. De ATENCION
        siempre se vuelve a REPOSO. Probado en los seis caminos de fallo.
  - [x] Un hilo trabajador efimero por turno. Sin bucle `asyncio` persistente.
  - [x] **Ningun hilo trabajador toca un widget.** Se cumple por construccion: el
        orquestador no importa nada de la GUI, y una prueba analiza su AST y falla si
        aparece un import de tkinter, customtkinter o gui.
  - [x] Ninguna excepcion sube hasta el `mainloop`.
  - [x] Maximo 2 rondas de tool calling; al agotarse responde con el texto disponible.
- Gates: `pytest tests/test_orchestrator.py` con dobles de STT, LLM y TTS.
- Human checks: H-08
- Risk triggers: **si** — concurrencia. Auditoria del modelo obligatoria.
- STOP when: la GUI se congele y la causa no sea evidente en una sesion de trabajo.

### T-10 - Interfaz de escritorio

- Status: **done** (2026-08-14). Veredicto: **APTO** (commit `d51cbf5`).
  **Defecto real encontrado al ejecutar la ventana**: con el escalado de Windows al
  133 %, la altura de 680 se dibujaba de 850 px reales y el boton de hablar quedaba
  debajo de la barra de tareas. Ahora la altura se calcula contra la pantalla real.
  Evidencia visual: `docs/evidencia/T-10-ventana.png`.
  Pendientes **H-09** y **H-10** (son de vista y de uso: los hace la duena).
- Depends on: T-09
- Scope: `gui/desktop_app.py`, `main.py`
- Acceptance:
  - [x] Ventana CustomTkinter en modo claro con la paleta pastel de `config.py`.
  - [x] Los 4 estados son distinguibles a simple vista, sin leer texto, **por color
        y por forma**. Usa la tabla de la seccion 11 del spec (corregida el 2026-08-13):
        cada estado tiene color propio y forma propia. Que dos estados compartan color
        es un NO APTO automatico: incumple H-09 y deja fuera a personas con daltonismo.
        **Verificado midiendo el lienzo**: 4 colores distintos y 4 figuras distintas.
        Queda una prueba automatica que falla si dos estados comparten color.
  - [x] Boton push-to-talk funcional; la barra espaciadora hace lo mismo (ignorando
        el eco de repeticion de teclas de Windows).
  - [x] Panel de conversacion con el historial visible.
  - [x] Los errores aparecen como mensajes amables, sin trazas tecnicas.
  - [x] `python main.py` levanta la aplicacion. Verificado: ventana abierta y
        capturada.
- Gates: `python -m compileall .`
- Human checks: H-09, H-10
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### T-11 - Modulo de exploracion del Transformer

- Status: **done** (2026-08-14). Veredicto: **APTO**.
- Nota de trazabilidad: el codigo entro por error dentro del commit de T-03
  (`6d0cf88`) y quedo sin veredicto. Se cerro y se le dio commit propio en `f1a9f43`.
- Verificacion independiente, ejecutada y no reportada:
  `python -m exploration.transformer_lab` -> exit 0; BETO con
  `attn_implementation="eager"` -> 12 capas de `(1, 12, 20, 20)`; embeddings
  `(1, 20, 768)`; la fila de atencion suma `1.000000`; el PNG se regenera
  identico byte a byte (89415 bytes); `compileall` exit 0. Salida completa
  versionada en `docs/evidencia/T-11-salida-transformer_lab.txt`.
- Correcciones aplicadas al cerrar, declaradas como excepcion del Arquitecto sobre
  el product plane (mismo criterio que en T-03):
  - Aviso en la salida del nivel 1: los tokens tipo `ÃŃa` no son un error de
    codificacion sino la representacion byte-level BPE del UTF-8. Sin ese aviso, la
    salida proyectada en la sustentacion parece un programa roto.
  - `README.md` afirmaba que este modulo no estaba implementado. Era falso en un
    repositorio publico.
- Depends on: T-01 (cerrada). No depende de `config.py` ni de ningun modulo de `core/`.
  Toca un unico archivo que nadie mas toca, asi que no hay conflicto posible.
- Despacho: **Ingeniero**, en paralelo con T-03.
- **Criterio de mayor peso de la rubrica (25%). No se recorta bajo ninguna circunstancia.**
- Scope: `exploration/transformer_lab.py`
- Acceptance:
  - [x] Nivel 1: tokenizador real de `Qwen/Qwen2.5-72B-Instruct` (sin pesos). Imprime
        tokens e IDs de una frase en espanol del propio proyecto. 30 tokens.
  - [x] Nivel 2: `dccuchile/bert-base-spanish-wwm-cased` cargado **obligatoriamente**
        con `attn_implementation="eager"`, con `output_attentions=True`. Sin ese
        argumento el modelo devuelve `None` en silencio (verificado en T-01).
        Imprime la forma del tensor de embeddings y explica que significa cada dimension.
  - [x] Genera un mapa de calor PNG de una capa y cabeza concretas, con los tokens
        etiquetados en ambos ejes. Capa 6, cabeza 4: cabeza de token anterior, la
        franja iluminada a la izquierda de la diagonal se ve a simple vista.
  - [x] Corre solo, sin la GUI, con el comando documentado en el README.
  - [x] Cada seccion tiene un comentario que explica el concepto, no solo el codigo.
- Gates: ejecucion del script; se conserva la salida y el PNG como evidencia.
- Human checks: H-11
- Risk triggers: ninguno. **Riesgo cerrado en T-01**: `torch 2.13.0+cpu` instalado y
  la extraccion de atencion sobre BETO verificada de extremo a extremo.
- STOP when: ninguna prevista.

### T-12 - Cierre del nucleo: errores y README

- Status: **done** (2026-08-14). Veredicto: **APTO**.
- **Hallazgo de la auditoria de errores**: de los 7 fallos de la seccion 13 faltaba
  uno en el codigo, el **reintento unico** ante respuesta vacia del LLM. Estaba
  escrito en el diseno desde el principio. Lo encontro auditar contra la lista, uno
  por uno, en vez de contra el recuerdo. Implementado y probado.
- Cobertura completa documentada en `docs/evidencia/T-12-cobertura-de-errores.md`,
  con la fila de cada fallo, donde se atiende y como se verifico. Incluye lo que
  **no** se cubre, dicho de frente.
- Depends on: T-10, T-11
- Scope: `README.md`, retoques de manejo de errores donde falte
- Acceptance:
  - [x] Los 7 fallos de la seccion 13 del diseno estan cubiertos con mensaje propio.
  - [x] Desconectar la red a mitad de un turno no rompe la aplicacion. **No se
        simulo**: se apunto el motor a un puerto cerrado para provocar un fallo de
        conexion real a mitad de turno. Aviso en lenguaje llano, vuelta a REPOSO,
        aplicacion utilizable.
  - [x] README permite instalar y ejecutar desde cero sin pasos no documentados.
        Verificado en un entorno virtual limpio, creado desde cero solo con
        `requirements.txt`: los 16 imports funcionan, las 59 pruebas pasan y todos
        los modulos del proyecto cargan.
- Gates: suite completa de `pytest`; `python -m compileall .`
- Human checks: H-12
- Risk triggers: ninguno
- STOP when: ninguna prevista.

### Auditoria de cierre de la Fase 1 (2026-08-14)

Auditoria completa pedida por la duena antes de autorizar la Fase 2. Alcance: todo
`config.py`, los seis modulos de `core/`, `gui/`, `main.py`, `exploration/`, los cinco
archivos de `tests/`, el README, el `.gitignore` y la coherencia de `.agents/`.

**Veredicto: NO APTO** — tres defectos de producto, todos fuera del codigo que corre.
Corregidos en el commit `72f1134`:

1. El README declaraba un modelo predeterminado que la aplicacion no usa. El commit
   `88ac9b4` cambio `config.py` a Qwen3.8 y no toco el README. Afectaba a un criterio
   de la rubrica en un repositorio publico, y habria contaminado el informe tecnico
   (T-16), que se escribe desde el documento de diseno — el cual citaba tres modelos
   que esta cuenta no puede usar.
2. `Pillow` no estaba en `requirements.txt` pese a importarse en `gui/desktop_app.py`.
   Se instalaba de rebote via matplotlib, con la version suelta. Riesgo directo
   contra H-18 (instalar en otra maquina siguiendo solo el README).
3. Precio del STT diez veces inflado en el README y en el documento de diseno.

Verificado de forma independiente, no por reporte: 70 pruebas verdes en 4.75 s;
`compileall` exit 0; `.env` nunca versionado; barrido de secretos sobre **todos** los
commits del historial, limpio.

Lo que la auditoria confirmo como solido: la cobertura de los 7 fallos previstos y su
tabla de evidencia, que declara de frente lo que NO cubre; la separacion de hilos, que
se cumple por construccion y no por disciplina; y una suite de pruebas que verifica
invariantes reales (una lee el AST del orquestador y falla si aparece un import de la
GUI; otra falla si dos estados llegaran a compartir color).

Cuatro incoherencias del control plane reparadas en el mismo cierre: el comando del
gate en `AGENTS.md` apuntaba a una carpeta inexistente y devolvia exit 0 igualmente;
`AGENTS.md` daba por pendiente una autenticacion de GitHub ya hecha; H-10 y H-11
figuraban a la vez firmadas y pendientes; y este criterio de T-10 estaba sin marcar
pese a estar verificado y firmado.

## Cierre de Fase 1 — fecha limite 22 de agosto

- [x] **T-01 a T-12 en APTO** (2026-08-14, ocho dias antes de la fecha limite).
- [ ] Checks humanos: **H-01 a H-09 firmados** tras el uso real del 2026-08-14.
      Quedan H-10 y H-11 (en contradiccion, ver `TESTING.md`) y H-12 en su version
      manual, con el wifi apagado de verdad. Falta ademas **reprobar las pruebas 2.3,
      5.1 y 5.3** con las correcciones ya aplicadas.
- [x] El pipeline completo funciona de extremo a extremo. Verificado sin GUI con los
      modulos reales en 21.8 s; falta la pasada con voz humana real (parte de H-10).
- [x] Auditoria de tarea con gate ejecutado en cada una; commit y push por tarea.
- [x] **Decision explicita**: la fase cerro con margen, asi que la Fase 2 **no se
      recorta**. Entra completa: T-13, T-14 y T-15.

---

# FASE 2 - VALOR AGREGADO (23 al 25 de agosto)

Solo empieza si la Fase 1 cerro. En este orden estricto: lo que no entre, se descarta.

### T-13 - Pestana Laboratorio en la GUI

- Status: **construida y verificada, veredicto EN SUSPENSO** (2026-08-14).
  Se implemento antes de que la duena pidiera detener la Fase 2, asi que su cierre
  formal espera su OK. Verificado con un `mainloop` real: 20.3 s el primer analisis
  (carga de BETO) y 0.8 s los siguientes; la ventana latio 309 veces mientras
  calculaba, o sea no se congelo. `exploration/transformer_lab.py` se refactorizo para
  exponer su API y **no duplicar el calculo**; su salida de consola quedo identica
  byte a byte, comprobado contra la evidencia anterior.
  **Aviso**: si se aprueba el rediseno de ventana que pidio la duena, esta pestana
  desaparece como tal y su contenido pasa a verse junto a la conversacion.
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

- Status: blocked (Fase 2 sin abrir)
- Depends on: T-07, T-09
- Scope: `tools/manifest.py`, `tools/system_skills.py`, `tests/test_tools.py`
- **ALCANCE AMPLIADO a peticion de la duena (2026-08-14): cuarta herramienta
  `calcular`.** Motivo: probo "raiz cuadrada de 3340" y el modelo respondio "no tengo
  calculadora pero puedo dar una respuesta aproximada". Un LLM no calcula, predice
  texto. No hace falta ningun servicio externo: Python es la calculadora.
  **Restriccion de seguridad, no negociable: nada de `eval` ni `exec` sobre lo que
  devuelva el modelo.** La expresion se analiza con `ast` contra una lista blanca de
  operaciones y funciones matematicas. Es la misma clase de riesgo que `abrir_kiosk`.
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

### T-19 - Rediseno visual y de distribucion (NUEVA, pedida el 2026-08-14)

- Status: **propuesta, sin abrir**. Requiere el OK de la duena.
- Depends on: cierre de la Fase 1 (hecho)
- Scope: `gui/desktop_app.py`, `config.py`, posible `gui/assets/`
- Motivo: la duena considera la interfaz "limpia y profesional" pero sin personalidad,
  y quiere que la presentacion sea mas vistosa.
- Acceptance:
  - [ ] Estetica con la tematica que pidio (paleta turquesa/rosa del personaje).
  - [ ] Modulo de estado mas grande.
  - [ ] **Sin pestanas**: conversacion y laboratorio visibles a la vez.
  - [ ] El mapa de atencion se abre expandido sobre la ventana, con boton de cerrar
        visible.
  - [ ] Los cuatro estados siguen distinguiendose por color Y forma (H-09 no se
        negocia: sigue siendo NO APTO automatico que dos compartan color).
- **Punto abierto que hay que decidir ANTES de implementar**: el repositorio es
  publico y el diseno del personaje es propiedad de Crypton Future Media. Subir arte
  de terceros a un repositorio publico no procede. Opciones: arte original generado
  por codigo con esa estetica, o una imagen cuyos derechos tenga la duena.
- Sobre la voz: no existe un TTS libre con la voz del personaje. Lo viable es subir
  tono y ritmo de una voz de edge-tts. Ya preparado en `config.py` (`TONO_TTS`,
  `RITMO_TTS`), sin aplicar todavia en `core/tts_engine.py`.
- Risk triggers: ninguno tecnico. El riesgo es de alcance: es la clase de tarea que
  se come los dias que hacen falta para el informe y el video.

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
