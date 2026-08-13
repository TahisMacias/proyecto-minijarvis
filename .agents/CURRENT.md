# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-13
source_commit: pre-primer-commit (repositorio recien inicializado)
assurance: Lean
active_plan: PLAN_v0.1-fundamentos.md
active_task: T-01
last_verdict: none
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico, vacio)
```

## Next action

1. Ejecutar **T-01**: crear `.venv` y verificar con evidencia real cuales de las
   librerias del stack instalan en Python 3.14.5, para decidir el interprete definitivo.

## Blockers

- **Ninguno bloqueante.** Los dos bloqueos anteriores se resolvieron el 2026-08-13:
  GitHub autenticado y `TOGETHER_API_KEY` validada contra la API.
- Riesgo abierto (no bloqueo): el stack sobre Python 3.14.5 sigue sin verificarse.

## Current facts

- Repositorio Git local inicializado el 2026-08-13, rama `main`, sin commits aun.
- Remoto `origin` configurado y verificado alcanzable; el repo remoto esta vacio.
- No existe codigo de producto. Solo el enunciado, la sintesis y el control plane.
- Python instalado: 3.14.5. Su compatibilidad con el stack **no esta verificada**.
- El repositorio vive dentro de OneDrive.
- Skills instaladas: `agents-workflow` (proyecto), `brainstorming` y `caveman` (global).

## Open findings

- `Proyecto_MiniJARVIS.pdf` y `Sintesis del proyecto.md` estan en la raiz. Podrian
  moverse a `docs/`, pero eso es reorganizacion de producto: requiere tarea propia.
- La sintesis del equipo propone Gmail y Google Calendar como herramientas. Ambas
  exigen OAuth, que es la integracion mas cara en tiempo de todo el catalogo. Aun
  no esta decidido si entran en el alcance real.

## Human actions

- [x] Autenticacion con GitHub. `gh` v2.97.0, cuenta `TahisMacias`, scopes `repo` y
      `workflow`. Verificado 2026-08-13.
- [x] `TOGETHER_API_KEY` en `.env` local, 50 caracteres. Validada contra
      `GET /v1/models` -> HTTP 200. Verificado 2026-08-13.
- [x] Proveedor de STT decidido: `openai/whisper-large-v3` en Together AI.
      Disponible en la cuenta.
- [ ] Verificar saldo en Together AI la vispera de la sustentacion (26 ago).
- [ ] No reactivar OneDrive durante el proyecto.
