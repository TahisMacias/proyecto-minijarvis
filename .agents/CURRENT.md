# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-13
source_commit: 16e449a (limpio, sincronizado con origin/main)
assurance: Lean
active_plan: PLAN_v1.0-entrega-27ago.md
active_task: T-01
last_verdict: none
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico)
deadline: 2026-08-27
```

## Next action

1. Ejecutar **T-01**: crear `.venv`, intentar instalar el stack completo y verificar
   acceso al microfono. Es un spike: su salida es la decision de que interprete usar.
   Bloquea a todas las demas tareas del plan.

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
- Python instalado: 3.14.5. **Compatibilidad con el stack aun sin verificar.**
- No existe codigo de producto todavia.

## Open findings

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
