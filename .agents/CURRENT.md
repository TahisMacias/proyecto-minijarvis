# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-13
source_commit: 3726302 (limpio, sincronizado con origin/main)
assurance: Lean
active_plan: PLAN_v1.0-entrega-27ago.md
active_task: T-03 y T-11 (en paralelo)
last_verdict: T-02 APTO
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico)
deadline: 2026-08-27
```

## Next action

1. El **Ingeniero** orquesta dos pistas en paralelo:
   - **T-03** `config.py` (riesgo: credenciales, exige auditoria del modelo)
   - **T-11** `exploration/transformer_lab.py` (25% de la rubrica, independiente
     del pipeline: no toca ningun archivo compartido)

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

- **Pendiente de aplicar a `config.py`**: la paleta gano un quinto acento, durazno
  `#FFF3E0`, para el estado ATENCION. El `config.py` entregado en T-03 asigna rosa
  palido tanto a RESPONDIENDO como a ATENCION, siguiendo el brief original.
  Es una correccion de una linea; se despacha cuando el Ingeniero cierre T-03.
  Motivo del cambio en `docs/specs/...-design.md` seccion 11.

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
