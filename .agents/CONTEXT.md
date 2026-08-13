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
