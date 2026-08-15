# CONTEXT - registro cronologico

Operacion normal es append-only. Las entradas nuevas van al final.
Solo un MAINTAIN o COMPACT explicito puede resumir entradas viejas, y debe preservar
fechas, decisiones, riesgos abiertos, referencias a tareas/commits y un puntero al archivo.

## 2026-08-13 - INIT (agents-workflow 2.0.0-dev)

- Changed: creado el control plane completo en `.agents/`. Inicializado el repositorio
  Git local en rama `main`. Creado `.gitignore` con `.env` excluido desde el primer commit.
  Configurado el remoto `origin`.
- Decisiones y motivo:
  - **Assurance Lean.** Proyecto academico, sin datos sensibles ni usuarios reales.
    Standard o Strict gastarian tokens sin reducir riesgo real.
  - **GitHub publico** en `https://github.com/TahisMacias/proyecto-minijarvis`, elegido
    por la duena. Cumple el requisito de historial compartido con el docente y evita
    gestionar invitaciones de colaborador.
  - **Semana 1 desde cero.** El milestone v0.1 se limita al entregable que pide el PDF
    para esta etapa: propuesta tecnica de una pagina y prototipo del modulo de exploracion.
  - **T-01 antes que todo lo demas.** La maquina tiene Python 3.14.5, una version lo
    bastante nueva como para que `torch` y las librerias de audio puedan no tener wheels.
    Verificar eso primero cuesta minutos; descubrirlo en la Semana 2 cuesta la entrega.
  - **No se escribio codigo de producto.** Peticion explicita de la duena: fase de
    planeacion primero.
- Evidence:
  - `git init -b main` -> "Initialized empty Git repository"
  - `git ls-remote https://github.com/TahisMacias/proyecto-minijarvis.git` -> exit 0,
    sin refs. El repo existe, es alcanzable y esta vacio.
  - `git --version` -> 2.54.0.windows.1
  - `python --version` -> 3.14.5
  - `gh --version` -> no instalado
- Unresolved:
  - Autenticacion con GitHub sin resolver; bloquea T-06.
  - Sin `TOGETHER_API_KEY`; bloquea la Semana 2.
  - Proveedor de STT sin decidir.
  - Alcance real de las herramientas Gmail/Calendar sin decidir (OAuth es caro en tiempo).
  - El repositorio vive en OneDrive; riesgo conocido de conflictos con `.git`.
- Next: ejecutar T-01 y registrar la evidencia de instalacion.

## 2026-08-13 - BRAINSTORMING (ruta architectural)

- Changed: escrito `docs/specs/2026-08-13-mini-jarvis-design.md`. Registrada la jerarquia
  de tres niveles en AGENTS.md. Corregidos dos hechos del entorno con evidencia real.
- **Dato nuevo que cambio todo: la entrega es el 27 de agosto.** Son 14 dias, no las
  3 semanas del cronograma del PDF. La estimacion de construccion da 12.25 dias sobre 14.
- Decisiones y motivo:
  - **Alcance de tools recortado de 7 a 3** (telemetria, busqueda web, kiosk), ninguna
    con OAuth. Motivo: el catalogo de herramientas no aparece en la rubrica —el enunciado
    lo marca opcional— mientras que Gmail y Calendar cuestan 2-3 dias de OAuth.
  - **Push-to-talk + `openai/whisper-large-v3`.** Se evaluo `nvidia/nemotron-3.5-asr-
    streaming-0.6b`, que si existe en Together AI y si soporta espanol (40 language-locales).
    Se descarto por precision: 0.6B en un aula con ruido, contra un large-v3 batch. La
    diferencia de costo resulto irrelevante: ~$1.00 contra ~$0.30 en todo el proyecto.
  - **Exploracion en dos niveles.** El modelo de produccion es una API y no expone pesos
    de atencion. Nivel 1: tokenizador real de Qwen (sin `torch`). Nivel 2: BETO local con
    `output_attentions=True`. La limitacion se documenta en el informe en vez de esquivarse.
  - **Hilos trabajadores en lugar de bucle `asyncio` persistente.** Se aparta de la
    sintesis original del equipo. Motivo: Tkinter exige `mainloop` en el hilo principal
    y widgets intocables desde otros hilos; sostener `asyncio` en paralelo obliga a dos
    modelos de concurrencia conviviendo. Aprobado explicitamente por la duena.
  - **Tres fases con fecha de corte**: nucleo 22 ago, valor agregado 25 ago, cierre 27 ago.
    Motivo: menos de dos dias de holgura. Si falta un extra la entrega cumple; si falta
    el pipeline no hay proyecto.
  - **Cuatro controles de sustentacion** en la GUI, cada uno mapeado a una pregunta guia
    de la seccion 12 del enunciado.
- Evidence:
  - `docs.together.ai/docs/inference/transcription/overview` -> IDs exactos de modelos STT
  - `together.ai/models/openai-whisper-large-v3` -> $0.015/min
  - `together.ai/models/nvidia-nemotron-35-asr` -> $0.0045/min, 40 language-locales
  - `Get-Process OneDrive` -> no corre; registro `Personal` -> si apunta a OneDrive;
    atributos de la carpeta -> `524304` = Directory + RECALL_ON_DATA_ACCESS
  - `winget list GitHub.cli` -> v2.97.0 instalado, ausente del PATH de la sesion
  - `git check-ignore -v .env` -> `.gitignore:2:.env` confirmado
- Unresolved:
  - `PLAN_v0.1-fundamentos.md` quedo obsoleto: se escribio antes de conocer la fecha de
    entrega y el alcance real. Debe reemplazarse por un plan de tres fases.
  - Sigue sin verificarse el stack sobre Python 3.14.5 (T-01).
  - Autenticacion de GitHub pendiente (`gh auth login` tras reiniciar la terminal).
  - `TOGETHER_API_KEY` aun no provista.
- Next: la duena revisa el spec. Luego se reescribe el plan por fases.

## 2026-08-13 - PUBLICACION Y REPLANIFICACION

- Changed: repositorio publicado en `origin/main`. `PLAN_v0.1` archivado y reemplazado
  por `PLAN_v1.0-entrega-27ago.md` (18 tareas, 3 fases). `TESTING.md` reescrito con
  H-01 a H-18 y R-01. Anadido `core/audio_capture.py` al diseno.
- Decisiones y motivo:
  - **El PDF del enunciado se saco del repositorio.** Es documento del docente y el
    repositorio es publico; republicarlo no corresponde. Se purgo del historial con
    `git filter-branch` — seguro porque nada se habia publicado aun— y se anadio a
    `.gitignore`. El archivo se conserva en local. Decision de la duena.
  - **Captura de audio separada del cliente STT.** Al desglosar las tareas quedo claro
    que gestionar dispositivo y buffer no es lo mismo que hacer una llamada HTTP.
    Refinamiento del diseno aprobado, no cambio de alcance.
  - **`PLAN_v0.1` archivado sin ejecutar.** Se escribio antes de conocer la fecha de
    entrega; planificaba una "Semana 1" de un cronograma de 3 semanas inexistente.
  - **T-04 (memoria) y T-05 (captura) van temprano** aunque no sean criticos: son las
    piezas mas faciles de verificar sin APIs, y dan gates deterministas reales pronto.
  - **T-09 (orquestador) marcada como la de mayor riesgo tecnico** del plan, con
    auditoria del modelo obligatoria. Es donde el proyecto puede congelarse.
- Evidence:
  - `git filter-branch` -> reescritos 3 commits; `git log --all --name-only` sin el PDF
  - PDF local restaurado desde respaldo: 395049 bytes, identico al original
  - barrido previo al push: `.env` no rastreado, 0 coincidencias de la clave en el
    historial, sin patrones de secreto en archivos rastreados
  - `git push -u origin main` -> `[new branch] main -> main`
  - `gh repo view` -> `visibility: PUBLIC`, 4 commits publicados
- Riesgo observado durante la operacion:
  - `git filter-branch` hizo un reset del working tree al reescribir HEAD y borro el
    PDF local. Se recupero del respaldo hecho antes de la operacion.
    **Regla aprendida:** respaldar siempre cualquier archivo que se purgue del
    historial, aunque la operacion se anuncie como que no toca el working tree.
- Unresolved:
  - El stack sobre Python 3.14.5 sigue sin verificarse (T-01, bloquea todo).
  - `Sintesis del proyecto.md` conserva decisiones ya superadas (`asyncio`, 7 tools).
    Sigue versionado como documento historico.
- Next: ejecutar T-01.

## 2026-08-13 - T-01 APTO (spike de entorno)

- Changed: creado `.venv/` con los 11 paquetes del stack. Registradas las versiones
  verificadas en `AGENTS.md`. Cerrado el riesgo mayor del proyecto.
- **Decision: se mantiene Python 3.14.5.** No hace falta instalar otro interprete.
  Todo el stack tiene wheels nativos `cp314`, incluido `torch 2.13.0+cpu`.
- Ejecutada por el Arquitecto y no delegada al Obrero: es diagnostico cuyo producto
  es una decision, y su interpretacion requiere juicio sobre que significa cada fallo.
- Evidence:
  - `pip install` de los 11 paquetes -> exit 0. Instalacion de `torch`+`transformers`
    tomo 5.1 min.
  - imports de los 10 modulos -> todos OK
  - `sounddevice.query_devices()` -> 10 entradas; captura de 0.5s a 16 kHz -> 8000
    frames con senal no nula
  - `OpenAI(base_url="https://api.together.xyz/v1")` -> construye correctamente en 3.0.0
  - `edge_tts.list_voices()` -> 45 voces `es-*`, `es-MX-DaliaNeural` presente
  - tokenizador de Qwen -> 14 tokens para 56 caracteres, con marcador `Ġ` de espacio
  - BETO -> embeddings `(1, 20, 768)`, 12 capas de `(1, 12, 20, 20)`, filas suman 1.0
  - heatmap PNG generado; muestra estructura real (`bate` <-> `##ria` de "bateria")
- **Hallazgos que cambian tareas futuras:**
  1. `transformers 5.x` usa SDPA por defecto y devuelve `None` en `output_attentions`
     **sin lanzar error**. Obliga a `attn_implementation="eager"`. Anadido como
     criterio de aceptacion explicito de T-11 y a Learned safeguards.
  2. `openai` subio a 3.0.0 (major). El patron `OpenAI(base_url=...)` sigue vigente.
  3. `$?` no es fiable tras un exe nativo en PowerShell 5.1: dos paquetes validos
     aparecieron como fallidos en la primera comprobacion. Se rehizo con
     `$LASTEXITCODE`. Regla registrada.
- Nota de proceso: `requirements.txt` se movio de T-01 a T-02 para respetar la regla
  de que el Arquitecto no edita el product plane. Las versiones verificadas viven en
  `AGENTS.md` como fuente de verdad.
- Unresolved: ninguno nuevo.
- Next: despachar T-02 al Obrero.

## 2026-08-13 - T-02 APTO y activacion del nivel Ingeniero

- Changed: esqueleto del repositorio creado por el Obrero (7 archivos). Registrada en
  `AGENTS.md` la tabla de cuando se activa el Ingeniero.
- **Defecto de proceso detectado por la duena, no por mi.** Despache T-02 del
  Arquitecto directo al Obrero, saltandome el nivel Ingeniero, y ademas anuncie que
  yo mismo lo auditaria. Eso contradice la regla que yo habia escrito en `AGENTS.md`:
  "el Obrero nunca audita su propio trabajo, devuelve el capsule al Ingeniero".
  El atajo era defendible para una tarea de andamiaje con gates binarios; **no
  declararlo no lo era**. Se añadio una tabla explicita para que la decision no quede
  al criterio del momento, y la excepcion quedo declarada en el propio brief de T-02.
- **Hallazgo de planificacion derivado:** al revisar el grafo de dependencias para
  justificar el nivel Ingeniero, se descubrio que **T-11 solo depende de T-01**, ya
  cerrada. Es decir, el modulo de exploracion —el 25% de la rubrica— estaba
  desbloqueado desde el principio y podia construirse en paralelo con todo el
  pipeline, sin tocar un solo archivo compartido. Estaba programado para el final sin
  ninguna razon tecnica. Se adelanta.
- Veredicto T-02: **APTO**. Verificacion independiente, no por reporte del Obrero:
  `git status --porcelain` -> exactamente 7 entradas, sin desborde de alcance;
  `compileall -q core tools gui exploration` -> exit 0; `.env` y `.venv` ausentes;
  `import core, tools, gui, exploration` -> ok.
- Aportes del Obrero fuera del brief, aceptados por mejorar el objetivo:
  - Paso de `Set-ExecutionPolicy` en el README: sin el, `Activate.ps1` falla bajo la
    politica por defecto de Windows y el README no seria reproducible en otra maquina.
  - Reporto que `.env` contiene una clave real y verifico que no esta en el historial,
    **sin reproducir el valor** en ningun archivo ni en su reporte.
- Unresolved: ninguno nuevo.
- Next: el Ingeniero orquesta T-03 y T-11 en paralelo.

## 2026-08-13 - Correccion de diseno: paleta de estados

- Changed: `docs/specs/...-design.md` seccion 11 y criterio de aceptacion de T-10.
- **Defecto detectado por el Obrero durante T-03**, no por el Arquitecto ni por el
  Ingeniero: la seccion 11 del spec describia la senal visual de cada estado pero
  **no asignaba color a RESPONDIENDO ni a ATENCION**. El mapeo provisional que el
  Arquitecto puso en el brief los dejaba compartiendo rosa palido.
- Por que importa: H-09 exige distinguir los cuatro estados sin leer texto. Dos
  estados del mismo color reprueban ese check y dejan fuera a personas con daltonismo.
- Decision: se anade durazno `#FFF3E0` para ATENCION. No es arbitrario — los acentos
  de la paleta son tintes Material de nivel 50 (green/pink/light-blue 50), y naranja 50
  extiende el sistema en vez de parchearlo. Se documenta la regla para futuros colores.
- Decision adicional: se anade una columna de **forma** por estado (circulo, puntos,
  onda, triangulo). El color por si solo no es accesible. T-10 marca como NO APTO
  automatico que dos estados compartan color.
- Pendiente: `config.py` conserva el mapeo antiguo. Correccion de una linea, se
  despacha cuando el Ingeniero cierre T-03, para no auditar contra un blanco movil.
- Observacion de proceso: el hallazgo vino del nivel mas bajo de la jerarquia. Es un
  argumento a favor de pedir a los Obreros que reporten inconsistencias del diseno
  aunque esten fuera de su alcance, en vez de limitarse a implementar el brief.

## 2026-08-14 - T-11 cerrada: existia, pero no estaba entregada

- Changed: `exploration/transformer_lab.py`, `README.md`,
  `docs/evidencia/T-11-salida-transformer_lab.txt` (commit `f1a9f43`).
- **Defecto de proceso encontrado al retomar:** CURRENT afirmaba que T-11 no se habia
  hecho y que el archivo no existia. `git show --stat 6d0cf88` demostro lo contrario:
  las 508 lineas del laboratorio y el PNG habian entrado dentro del commit de T-03,
  sin veredicto propio y sin gate ejecutado. Un archivo puede existir y aun asi no
  estar cerrado; y un commit puede arrastrar trabajo de otra tarea sin que nadie lo
  note. Regla derivada: antes de declarar que una tarea no se hizo, mirar el diff de
  los commits recientes, no solo el estado del arbol.
- Veredicto T-11: **APTO**. Verificacion ejecutada, no aceptada por reporte:
  `python -m exploration.transformer_lab` -> exit 0; 12 capas de atencion de
  `(1, 12, 20, 20)`; embeddings `(1, 20, 768)`; fila de atencion = `1.000000`;
  PNG regenerado identico byte a byte (89415 bytes); `compileall` exit 0.
  El mapa se inspecciono visualmente: la franja iluminada a la izquierda de la
  diagonal confirma que la capa 6 / cabeza 4 es una cabeza de token anterior, tal
  como el codigo afirma. La afirmacion del script y la imagen concuerdan.
- Dos correcciones aplicadas por el Arquitecto sobre el product plane, **declaradas
  como excepcion** (mismo criterio que en T-03):
  - La salida del nivel 1 mostraba tokens como `ÃŃa` sin explicarlos. No es un error:
    el tokenizador de Qwen es byte-level BPE y opera sobre bytes UTF-8. Pero esa
    salida se proyecta en la sustentacion, y sin explicacion parece un programa roto
    delante del tribunal. Se anadio un aviso que convierte el detalle en argumento.
  - `README.md` afirmaba que el laboratorio no estaba implementado. Era falso, y el
    repositorio es publico.
- Barrido de estado obsoleto en el plan: T-03 seguia como `ready` estando APTO, y
  T-04, T-05 y T-08 seguian `blocked (T-03)`. Corregido.
- Unresolved: la observacion sobre el nivel Ingeniero sigue abierta. En esta sesion
  no hubo despacho jerarquico, asi que no aporta evidencia ni a favor ni en contra.
- Next: push, y despachar T-04 (T-05 y T-08 pueden ir en paralelo, no comparten archivos).

## 2026-08-14 - Cinco modulos de core/ entregados, y un hallazgo que salva la demo

- Changed: `core/memory.py`, `core/audio_capture.py`, `core/stt_client.py`,
  `core/llm_engine.py`, `core/tts_engine.py`, `tests/`, `pytest.ini`,
  `requirements.txt`, `config.py`, `exploration/transformer_lab.py`.
  Commits `04f2fbc`, `f7230a7`, `ba169e1`, `5874a35`, `b620ac7`, `38715f7`, `a034533`.
- Ejecutado por el Arquitecto, **excepcion declarada** al reparto de roles: la duena
  pidio continuar con todo en una sola sesion. Cada tarea llevo su gate ejecutado, no
  reportado, y su commit propio. La separacion que si se mantuvo es la que importa:
  ninguna tarea se dio por buena sin evidencia reproducible.
- **HALLAZGO MAYOR (T-07): los dos modelos del plan no los sirve esta cuenta.**
  `Qwen/Qwen2.5-72B-Instruct` y `meta-llama/Llama-3.3-70B-Instruct` figuran en
  `GET /v1/models` —que es como se dieron por verificados el 2026-08-13— pero
  responden HTTP 400 "Unable to access non-serverless model". Estan en el catalogo de
  Together, no en su servicio compartido; usarlos exigiria pagar un endpoint dedicado.
  Se probaron catorce identificadores uno por uno hasta encontrar los que responden:
  `meta-llama/Llama-3.3-70B-Instruct-Turbo` y `Qwen/Qwen2.5-7B-Instruct-Turbo`.
  **Leccion general, aplicable mas alla de este proyecto: que un recurso aparezca en
  un listado no prueba que se pueda usar. Solo lo prueba ejercerlo.** De no haberse
  detectado ahora, habria aparecido como un 400 sin explicacion el dia de la demo.
- Consecuencia en cadena: el nivel 1 del laboratorio decia usar "el tokenizador del
  LLM de produccion" nombrando un modelo inaccesible. Se repunto al de
  `Qwen/Qwen2.5-7B-Instruct`, que es el del modelo alterno real. No se uso el de
  Llama porque su repositorio en Hugging Face esta restringido: se comprobo y
  devuelve "You are trying to access a gated repo". Una demostracion que depende de
  un permiso ajeno es fragil.
- Decisiones de implementacion que se apartan de lo previsto, con motivo:
  - `core/memory.py` **no importa `config.py`**, siguiendo la tabla de modulos del
    diseno, que lo lista sin dependencias. Efecto util: las pruebas corren en una
    maquina sin `.env` ni credenciales.
  - La reproduccion de voz usa **MCI** de Windows via `ctypes` en vez de anadir una
    libreria de audio: edge-tts devuelve MP3 y Windows ya sabe decodificarlo.
  - Se anadio `pytest` (no estaba en `requirements.txt` pese a que tres gates del
    plan lo exigen) y `pytest.ini` con `pythonpath = .`.
- Verificaciones que no se aceptaron por reporte: transcripcion real de audio
  sintetizado, reproduccion medida en 4.92 s para confirmar que bloquea, captura real
  de microfono releida con el modulo `wave`, y cambio de modelo en caliente con la
  conversacion viva.
- Unresolved: H-04 y H-07 pendientes de la duena (son de oido, nadie mas los puede
  hacer). El nivel Ingeniero sigue sin segunda observacion: esta sesion no uso
  jerarquia, asi que no aporta evidencia.
- Next: T-09, el orquestador. Es la tarea de mayor riesgo tecnico del plan.

## 2026-08-14 - Fase 1 completa: la aplicacion habla, escucha y responde

- Changed: `core/orchestrator.py`, `gui/desktop_app.py`, `main.py`, `README.md`,
  `tests/test_orchestrator.py`, `tests/test_paleta_estados.py`, evidencia.
  Commits `c351170` (T-09), `d51cbf5` (T-10) y el de T-12.
- **T-09, la tarea de mayor riesgo del plan, cerrada sin sobresaltos.** La regla de
  "ningun hilo toca un widget" no se dejo a la disciplina: el orquestador simplemente
  no tiene acceso a la GUI, y una prueba lee su AST para que siga siendo cierto. Es
  la diferencia entre una regla escrita y una regla que se cumple sola.
- **Tres defectos reales que solo aparecen al ejecutar, no al leer:**
  1. Una transcripcion de puros espacios pasaba como texto valido (la encontro una
     prueba de frontera).
  2. Con el escalado de Windows al 133 %, la ventana de 680 se dibujaba de 850 px y
     **el boton de hablar quedaba debajo de la barra de tareas**. La aplicacion habria
     parecido rota el dia de la demostracion sin estarlo. Ahora la altura se calcula
     contra la pantalla real.
  3. Al auditar los 7 fallos de la seccion 13 para T-12 faltaba uno: el **reintento
     unico** ante respuesta vacia del LLM. Estaba en el diseno y no en el codigo.
     Auditar contra la lista escrita, y no contra el recuerdo, es lo que lo encontro.
- Verificacion de red que no se simulo: se apunto el motor a un puerto cerrado para
  provocar un fallo de conexion **real** a mitad de turno. La aplicacion aviso con
  lenguaje llano, volvio a REPOSO y siguio utilizable.
- H-09 se verifico midiendo, no a ojo: se instrumento el lienzo y se comprobo que los
  cuatro estados activos usan cuatro colores y cuatro figuras distintas. Queda una
  prueba que falla si dos estados llegaran a compartir color: ese defecto ya ocurrio
  una vez en este proyecto y no deberia poder repetirse en silencio.
- Unresolved: H-04, H-07, H-09, H-10 y H-12 son de la duena (oido, vista y uso).
  Nadie mas los puede firmar.
- Next: cierre de la Fase 1 y decision sobre la Fase 2 (T-13 a T-15).

## 2026-08-14 - Cierre de la Fase 1

- La Fase 1 completa (T-01 a T-12) queda en APTO el 2026-08-14, ocho dias antes de su
  fecha limite del 22 de agosto. El 65 % de la rubrica que protege esta fase esta
  cubierto, y tambien el 25 % del laboratorio del Transformer.
- Nota de proceso: el commit de T-12 mezclo el plano de producto y el de control en
  un solo commit. Es una desviacion menor de la regla de dos planos; se deja anotada
  aqui en vez de reescribir el historial de un repositorio ya publicado.
- **La Fase 2 no arranca todavia, y es a proposito.** El plan dice que no empieza
  hasta que la Fase 1 este *completa y verificada*, y lo que falta para verificada son
  cinco checks humanos (H-04, H-07, H-09, H-10, H-12) mas H-11. Son de oido, de vista
  y de uso: ninguna prueba automatica los sustituye, y firmarlos por cuenta propia
  seria justo el tipo de atajo que este workflow existe para evitar.
- Decision ya tomada y escrita: como la fase cerro con margen, la Fase 2 entra
  completa (T-13 pestana Laboratorio, T-14 controles de sustentacion, T-15 tool
  calling). No se recorta.
