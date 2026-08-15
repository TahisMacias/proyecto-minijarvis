# AGENTS - Mini-JARVIS

## Operating mode

- Assurance: **Lean**
- Product plane owner: Obrero (codigo de la app, tests, assets)
- Control plane owner: Arquitecto (`.agents/`)

### Jerarquia de tres niveles

`agents-workflow` define dos planos (ejecutor / auditor). Este proyecto los reparte
en tres roles, sin romper esa separacion:

| Rol | Modelo | Responsabilidad | Puede editar |
|---|---|---|---|
| **Arquitecto** | Opus (sesion principal) | Planea, audita fases, decide alcance, commit y push | solo control plane |
| **Ingeniero** | Opus (subagente) | Orquesta obreros, audita cada tarea, arma audit capsules | solo control plane |
| **Obrero** | Sonnet (subagente) | Escribe codigo acotado y tareas repetitivas | solo product plane |

Reglas que sostienen la separacion:

- El Obrero **nunca** audita su propio trabajo. Devuelve un audit capsule al Ingeniero.
- El Ingeniero **nunca** escribe codigo de producto. Si detecta un defecto, reabre la
  tarea con un brief nuevo para el Obrero.
- Solo el Arquitecto hace `commit` y `push`. Nadie mas toca el historial de Git.
- Un cambio de alcance, arquitectura, seguridad o interfaces **para** y sube al
  Arquitecto; no lo resuelve el Ingeniero por su cuenta.
- Todo brief para el Obrero debe ser autocontenido: ID de tarea, objetivo, alcance
  permitido, criterios de aceptacion, gates y condiciones de STOP.

### Cuando se activa el Ingeniero

Levantar un Ingeniero cuesta un agente que arranca en frio y re-deriva contexto.
Esta tabla evita que la decision quede al criterio del momento:

| Situacion | Quien despacha |
|---|---|
| 2 o mas tareas paralelizables | **Ingeniero** |
| Tarea con `Risk triggers: si` (T-03, T-09, T-15, T-18) | **Ingeniero** |
| Ciclo de correccion tras un NO APTO | **Ingeniero** |
| Tarea unica, mecanica, con gates binarios | Arquitecto directo, **declarandolo en voz alta** |

La ultima fila es una excepcion, no la norma. Si el Arquitecto despacha directo,
debe decirlo explicitamente en el momento. Saltarse el nivel en silencio es el
defecto que esta tabla existe para prevenir (incidente del 2026-08-13 en T-02).
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
- Runtime: **Python 3.14.5 — CONFIRMADO en T-01 (2026-08-13).** Todo el stack instala
  con wheels nativos `cp314`. No hace falta bajar de version. Riesgo cerrado.
- Entorno virtual: `.venv/` en la raiz. Interprete: `.venv\Scripts\python.exe`.

### Versiones verificadas en T-01 (fuente de verdad para `requirements.txt`)

| Paquete | Version | Nota |
|---|---|---|
| `python-dotenv` | 1.2.2 | |
| `openai` | 3.0.0 | major nueva; `OpenAI(base_url=...)` verificado contra Together |
| `edge-tts` | 7.2.8 | `es-MX-DaliaNeural` presente entre 45 voces `es-*` |
| `customtkinter` | 6.0.0 | |
| `sounddevice` | 0.5.5 | 10 dispositivos de entrada; captura real verificada |
| `psutil` | 7.2.2 | |
| `duckduckgo-search` | 8.1.1 | |
| `tiktoken` | 0.13.0 | |
| `matplotlib` | 3.11.1 | heatmap PNG generado correctamente |
| `transformers` | 5.15.0 | ver trampa de `attn_implementation` abajo |
| `torch` | 2.13.0+cpu | CPU puro, sin CUDA. Suficiente para BETO. |
| `numpy` | 2.5.2 | |
| `pytest` | 9.1.1 | anadido en T-04: tres gates del plan lo exigen y no estaba. |
- Git: 2.54.0.windows.1, identidad `Tahis Macias <britany.macias@cenestur.edu.ec>`
- `gh` CLI: instalado v2.97.0 en `C:\Program Files\GitHub CLI\gh.exe`, pero **no estaba
  en el PATH** de la sesion del 2026-08-13 (se instalo con la terminal ya abierta).
  Requiere reiniciar la terminal. Autenticacion pendiente: `gh auth login`.
- Build/test quirks:
  - **OneDrive: riesgo dormido, no activo.** Verificado el 2026-08-13: el proceso
    OneDrive NO corre. Pero `Documentos` si esta redirigido a `C:\Users\brith\OneDrive\
    Documents` en el registro, y la carpeta tiene el atributo `RECALL_ON_DATA_ACCESS`
    (Files On-Demand). Si OneDrive vuelve a arrancar, empezara a sincronizar `.git`.
    No reactivarlo durante el proyecto.
  - Wheels de audio (`sounddevice`, `pyaudio`) y `torch` pueden no existir para 3.14.
- Ignored/generated: `.venv/`, `__pycache__/`, `*.wav`, `*.mp3`, `models/`, `.cache/`

## Learned safeguards

- **2026-08-13 (T-01). `transformers 5.x` no devuelve pesos de atencion por defecto.**
  El backend predeterminado es SDPA, que devuelve `None` en `output_attentions=True`
  **sin lanzar error**. Un fallo silencioso que habria costado horas en T-11.
  **Regla:** cargar el modelo con `AutoModel.from_pretrained(nombre,
  attn_implementation="eager")`. Verificado: con eager, `salida.attentions` trae
  12 capas de `(lote, 12 cabezas, tokens, tokens)` y cada fila suma 1.0.
- **2026-08-13. `$?` no es fiable tras un ejecutable nativo en PowerShell 5.1.**
  Al comprobar paquetes con `pip ... 2>&1`, dos resultaron "FALLA" siendo validos:
  redirigir stderr de un exe nativo envuelve cada linea en un ErrorRecord y pone `$?`
  en `$false` aunque el exit code sea 0.
  **Regla:** usar `$LASTEXITCODE` para juzgar exitos de comandos nativos, nunca `$?`.
- **2026-08-13.** Purgar el PDF del enunciado con `git filter-branch --index-filter`
  borro tambien el archivo del working tree: al reescribir HEAD, filter-branch resetea
  el arbol de trabajo. Se recupero del respaldo hecho minutos antes.
  **Regla:** antes de purgar cualquier archivo del historial de Git, copiarlo fuera del
  repositorio. No confiar en que `--index-filter` "solo toca el indice".
