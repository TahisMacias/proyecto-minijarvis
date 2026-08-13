# AGENTS - Mini-JARVIS

## Operating mode

- Assurance: **Lean**
- Product plane owner: executor (codigo de la app, tests, assets)
- Control plane owner: planner/auditor (`.agents/`)
- Local Git: required — inicializado 2026-08-13, rama `main`
- Backup: remote GitHub **publico** `origin` ->
  `https://github.com/TahisMacias/proyecto-minijarvis` (verificado vacio y alcanzable 2026-08-13)
- Sibling systems outside scope: ninguno

## Verification surface

- Gate command (objetivo, aun no ejecutable — se habilita en T-01):
  `python -m compileall mini_jarvis exploration`
- Covers: errores de sintaxis e imports rotos en el codigo versionado.
- Does not cover: calidad del audio, latencia real del pipeline, correccion de las
  respuestas del LLM, comportamiento de la GUI. Todo eso es verificacion humana —
  ver `.agents/TESTING.md`.
- Risk triggers requiring model audit:
  - manejo de credenciales / `.env` / cualquier cosa que toque API keys
  - `tools/system_skills.py` — ejecuta `subprocess`, envia correos y toma capturas
  - cierre de milestone y entrega academica

## Workflow

1. Leer CURRENT y su plan activo; expandir contexto solo si hace falta.
2. El executor completa UNA tarea acotada y commitea `[T-NN] ...`.
3. El executor devuelve un audit capsule: criterios, commits, archivos, diff, gates, riesgos.
4. El auditor verifica evidencia y devuelve APTO, NO APTO o BLOCKED.
5. El auditor actualiza `.agents/` con `[STATE] ...`; las correcciones de producto vuelven al executor.

Lean agrupa auditorias de bajo riesgo en el limite de fase. Los gates deterministas
igual corren en cada commit.

## Durable rules

- Rutas relativas al repositorio en todo archivo persistente.
- Staging selectivo. Preservar cambios no relacionados.
- Evidencia antes que afirmaciones. Declarar los checks que no se pudieron correr.
- Prohibido versionar credenciales, tokens, llaves privadas o datos personales.
  El PDF lo exige explicitamente (seccion 6 y seccion 11).
- CONTEXT es append-only salvo en MAINTAIN/COMPACT explicito y trazable.
- Historial de commits **progresivo**: el PDF descalifica un unico commit final.
  Un commit por tarea, con mensaje descriptivo en espanol.
- Los comandos de herramientas van en recetas locales fechadas y se re-verifican.

## Environment

- OS/shell: Windows 11 Pro 10.0.26200; PowerShell 5.1 + Git Bash
- Runtime: **Python 3.14.5** (riesgo abierto — ver `PLAN_v0.1` T-02)
- Git: 2.54.0.windows.1, identidad `Tahis Macias <britany.macias@cenestur.edu.ec>`
- `gh` CLI: NO instalado. Sin credential helper configurado.
- Build/test quirks:
  - El repositorio vive dentro de **OneDrive**. La sincronizacion puede bloquear o
    corromper archivos de `.git`. Pausar OneDrive durante operaciones largas de Git.
  - Wheels de audio (`sounddevice`, `pyaudio`) y `torch` pueden no existir para 3.14.
- Ignored/generated: `.venv/`, `__pycache__/`, `*.wav`, `*.mp3`, `models/`, `.cache/`

## Learned safeguards

- (vacio — se llena cuando un incidente produzca una regla reutilizable)
