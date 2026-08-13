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

- **Credenciales de GitHub sin configurar.** No hay `gh` CLI ni credential helper.
  El primer `git push` va a pedir autenticacion. Bloquea T-06, no bloquea T-01.
- **Ninguna API key disponible todavia.** Sin `TOGETHER_API_KEY` no hay pipeline.
  No bloquea la Semana 1, pero si bloquea la Semana 2 completa.

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

- [ ] Resolver autenticacion con GitHub: instalar `gh` CLI o crear un Personal
      Access Token. Necesario antes de T-06.
- [ ] Conseguir la `TOGETHER_API_KEY` en https://api.together.xyz y guardarla en
      `.env` local. **Nunca pegarla en el chat ni commitearla.**
- [ ] Decidir el proveedor de STT (Whisper de OpenAI requiere clave propia y saldo).
- [ ] Pausar la sincronizacion de OneDrive durante operaciones largas de Git.
