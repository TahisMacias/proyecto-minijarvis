# PLAN v0.1 - Fundamentos y diseno (Semana 1)

Status: active
Goal: cerrar el entregable de Semana 1 del PDF — propuesta tecnica de una pagina y
prototipo funcional del modulo de exploracion (tokenizacion/atencion) — sobre un
repositorio publicado con entorno verificado y sin credenciales expuestas.
Assurance: Lean

Regla de orden: **T-01 bloquea a todas las demas**. No se escribe codigo de producto
hasta saber sobre que interprete de Python corre el proyecto.

## Tasks

### T-01 - Decidir el interprete de Python verificando el stack real

- Status: ready
- Depends on: none
- Scope: `.agents/` (recetas y hallazgos), `requirements.txt` (borrador)
- Tipo: spike. Su salida es una decision, no codigo que se conserve.
- Acceptance:
  - [ ] Existe evidencia (salida real de `pip install`) de si estas librerias instalan
        en Python 3.14.5 en Windows: `customtkinter`, `edge-tts`, `openai`,
        `sounddevice` (o `pyaudio`), `tiktoken`, `transformers`, `torch`.
  - [ ] Queda registrada una decision explicita: seguir en 3.14.5 o fijar 3.12.
  - [ ] La version elegida queda escrita en `.agents/AGENTS.md` > Environment.
- Gates: `python -m venv .venv` seguido de la instalacion; se registra el codigo de salida.
- Human checks: H-01
- Risk triggers: si `torch` no tiene wheel para 3.14, T-04 queda bloqueado.
- STOP when: haya que instalar un Python nuevo en la maquina — eso lo decide la duena.

### T-02 - Esqueleto del repositorio ejecutable en otra maquina

- Status: blocked (espera T-01)
- Depends on: T-01
- Scope: `README.md`, `requirements.txt`, `.env.example`, arbol de carpetas vacio
  con `__init__.py` en `core/`, `tools/`, `gui/`, `exploration/`
- Acceptance:
  - [ ] `README.md` documenta: requisitos, creacion del venv, instalacion y ejecucion.
  - [ ] `requirements.txt` fija versiones que instalan limpio en la version de T-01.
  - [ ] `.env.example` lista cada variable requerida **sin un solo valor real**.
  - [ ] `git status` no muestra `.env` ni `.venv/` como no rastreados.
- Gates: `python -m compileall .`
- Human checks: H-02
- Risk triggers: ninguno
- STOP when: se necesite decidir el proveedor de STT (afecta que claves se declaran).

### T-03 - Carga segura de configuracion y credenciales

- Status: blocked (espera T-02)
- Depends on: T-02
- Scope: `config.py`
- Acceptance:
  - [ ] Las claves se leen de `.env` via variable de entorno; ninguna literal en codigo.
  - [ ] Si falta una clave, la app da un mensaje claro y no arranca a medias.
  - [ ] La paleta pastel y las constantes de UI viven aqui, en un solo lugar.
  - [ ] `git log -p` no contiene ninguna clave en ningun commit.
- Gates: `python -m compileall .` y `git grep -i -E "sk-|api_key\s*=\s*[\"']" `
- Human checks: none
- Risk triggers: **si** — toca manejo de credenciales. Requiere auditoria del modelo.
- STOP when: se detecte una clave ya commiteada; eso escala a la duena de inmediato.

### T-04 - Modulo de exploracion del Transformer

- Status: blocked (espera T-01)
- Depends on: T-01
- Scope: `exploration/transformer_lab.py`
- Es el criterio de mayor peso de la rubrica (25%). No se recorta.
- Acceptance:
  - [ ] Para una frase de ejemplo en espanol, imprime los tokens y sus IDs.
  - [ ] Muestra la forma (shape) del tensor de embeddings y explica que significa.
  - [ ] Extrae la matriz de self-attention (`output_attentions=True`) de al menos
        una capa y una cabeza, y la presenta de forma legible.
  - [ ] El script corre solo, sin la GUI, con un comando documentado en el README.
  - [ ] Cada seccion tiene un comentario que explica el concepto, no solo el codigo.
- Gates: ejecucion del script; se guarda la salida como evidencia.
- Human checks: H-03
- Risk triggers: dependencia de `torch`; si T-01 lo descarta, replantear con `tiktoken`
  para tokenizacion y buscar alternativa para atencion. **Eso cambia el alcance: STOP.**
- STOP when: `torch` no sea instalable en la version de Python elegida.

### T-05 - Propuesta tecnica de una pagina

- Status: blocked (espera T-01)
- Depends on: T-01
- Scope: `docs/propuesta-tecnica.md`
- Acceptance:
  - [ ] Una pagina. Cubre: eleccion de STT/LLM/TTS con justificacion tecnica,
        diagrama de arquitectura y flujo de conversacion.
  - [ ] Nombra modelo y proveedor exactos (requisito etico, seccion 11 del PDF).
  - [ ] Coherente con `.agents/APPCORE.md`; si difiere, gana el documento y se
        actualiza APPCORE.
- Gates: none (documento)
- Human checks: H-04
- Risk triggers: ninguno
- STOP when: la justificacion tecnica exija una decision de arquitectura no tomada.

### T-06 - Publicar el repositorio con historial limpio

- Status: blocked (espera T-02)
- Depends on: T-02
- Scope: configuracion de Git; sin archivos de producto
- Acceptance:
  - [ ] `git push -u origin main` completa contra
        `https://github.com/TahisMacias/proyecto-minijarvis`.
  - [ ] El repo remoto muestra mas de un commit con mensajes descriptivos.
  - [ ] Ningun archivo `.env` ni credencial visible en GitHub.
- Gates: `git log --oneline` y revision visual del repo remoto.
- Human checks: H-05
- Risk triggers: **si** — es una accion hacia afuera e irreversible en la practica
  (un secreto publicado ya no se recupera). Verificar antes de empujar.
- STOP when: falte autenticacion; la duena debe resolver credenciales de GitHub.

## Closure gate

- [ ] Todas las tareas APTO.
- [ ] Checks humanos H-01 a H-05 completos.
- [ ] Barrido de estado obsoleto: versiones, dependencias y comandos concuerdan
      entre README, `requirements.txt`, AGENTS y la realidad de la maquina.
- [ ] CURRENT, INDEX, APPCORE, TESTING y Git concuerdan.
- [ ] El repositorio publico refleja el trabajo de la semana.
