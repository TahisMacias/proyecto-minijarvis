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
