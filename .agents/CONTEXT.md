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
