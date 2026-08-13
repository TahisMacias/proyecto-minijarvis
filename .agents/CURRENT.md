# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-13
source_commit: 3726302 (limpio, sincronizado con origin/main)
assurance: Lean
active_plan: PLAN_v1.0-entrega-27ago.md
active_task: T-11
last_verdict: T-03 APTO
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico)
deadline: 2026-08-27
```

## COMO RETOMAR EN UNA SESION NUEVA

Di "continua el plan". Todo el estado vive aqui, no en ninguna conversacion.
Orden de lectura: este archivo -> `PLAN_v1.0-entrega-27ago.md` -> `AGENTS.md`.
El diseno completo esta en `docs/specs/2026-08-13-mini-jarvis-design.md`.

### Trabajo a medias al cerrar la sesion del 2026-08-13

1. **T-11 NO se hizo.** `exploration/transformer_lab.py` no existe. Su Obrero no
   entrego. Hay que redespacharlo. **Es el 25% de la rubrica y ya esta desbloqueado.**
2. **Decision abierta sobre la jerarquia de tres niveles.** El Ingeniero se detuvo a
   mitad de su primera tanda sin emitir veredictos; hubo que reanudarlo. Criterio ya
   acordado con la duena: si vuelve a fallar, se elimina el nivel intermedio y el
   Arquitecto despacha Obreros declarando cada despacho en voz alta. Un incidente no
   es patron; dos si.

## Next action

1. Redespachar **T-11**. Recordatorio critico: BETO debe cargarse con
   `attn_implementation="eager"` o `output_attentions` devuelve `None` en silencio.

## Blockers

- Ninguno. Los dos bloqueos de la sesion anterior se resolvieron el 2026-08-13.

## Current facts

- **Entrega: 27 de agosto de 2026.** 14 dias desde el inicio del proyecto.
- Diseno aprobado y versionado en `docs/specs/2026-08-13-mini-jarvis-design.md`.
- Plan activo de 18 tareas en 3 fases con fechas de corte: nucleo 22 ago,
  valor agregado 25 ago, cierre 27 ago.
- Repositorio publico en `https://github.com/TahisMacias/proyecto-minijarvis`,
  4 commits publicados, local y remoto sincronizados.
- `gh` CLI v2.97.0 autenticado como `TahisMacias`, scopes `repo` y `workflow`.
- `TOGETHER_API_KEY` en `.env` local, validada contra `GET /v1/models` (HTTP 200).
- Modelos verificados disponibles en la cuenta: `openai/whisper-large-v3`,
  `Qwen/Qwen2.5-72B-Instruct`, `meta-llama/Llama-3.3-70B-Instruct`.
- El enunciado en PDF **no esta versionado** a proposito: es material del docente y
  el repositorio es publico. Vive en local, excluido por `.gitignore`.
- **Python 3.14.5 confirmado como interprete definitivo** (T-01). Todo el stack
  instala con wheels nativos `cp314`, `torch 2.13.0+cpu` incluido. Riesgo cerrado.
- Entorno virtual creado en `.venv/` con los 11 paquetes instalados.
- La extraccion de self-attention sobre BETO esta verificada de extremo a extremo:
  T-11 es viable. Requiere `attn_implementation="eager"`.
- Microfono verificado: 10 dispositivos, Realtek por defecto, captura real correcta.
- Esqueleto del repositorio completo: `README.md`, `requirements.txt` con 12
  versiones fijadas, `.env.example`, y los cuatro paquetes importables.
- Aun no existe logica de aplicacion: no hay `config.py` ni `main.py`.

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
- [ ] Verificar saldo en Together AI la vispera de la sustentacion (26 ago).
- [ ] No reactivar OneDrive durante el proyecto.
- [ ] Reservar los dias 26 y 27 para informe, video y ensayo. Sin codigo.
