# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-28 (sesion 6, cierre de entrega)
source_commit: ver ultimo [STATE]; limpio y sincronizado con origin/main
assurance: Lean
active_plan: ninguno — PLAN_v1.0 archivado en archive/
active_task: ninguna — no queda trabajo de codigo
last_verdict: ENTREGADO. Los cuatro entregables de la seccion 8 del enunciado estan
  cubiertos salvo la sustentacion oral, que es un evento futuro.
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico)
deadline: 2026-08-27 (la duena entrego; ver nota de fechas mas abajo)
```

## COMO RETOMAR EN UNA SESION NUEVA

Di "continua". Orden de lectura: este archivo -> `AGENTS.md` -> `APPCORE.md`.
El plan cerrado esta en `archive/PLAN_v1.0-entrega-27ago.md`.

## Next action

**NO QUEDA TRABAJO DE CODIGO NI DE DOCUMENTOS.** Lo unico pendiente es la
**sustentacion oral**, que es un evento en vivo y no se puede automatizar.

Material listo para ese dia:

- `docs/Chuleta sustentacion - Mini-JARVIS.pdf` (3 paginas, para llevar en la mano)
- `docs/guion-sustentacion.md` (respuestas largas a las seis preguntas guia)

## Estado de la entrega

| Entregable (seccion 8 del enunciado) | Estado |
|---|---|
| Repositorio publico con README | entregado, 79+ commits |
| Informe tecnico | dos versiones, ver nota abajo |
| Video demo (2-4 min) | grabado y entregado por la duena |
| Sustentacion oral en vivo | PENDIENTE, evento futuro |

**Hay dos informes y sirven para cosas distintas.** `docs/informe-tecnico.md` y su
version en Word de 8 paginas cumplen el limite de 4 a 8 que pide el enunciado.
`docs/Informe Proyecto Mini-JARVIS.docx` (17 paginas) usa la plantilla institucional
de CENESTUR que la duena debia rellenar. Se entrego el segundo porque el formato del
instituto manda sobre la regla general del enunciado.

## Riesgo aceptado en el cierre

**El closure gate del plan no se cumplio y se cierra igual.** Es una decision de la
duena, tomada al entregar, y queda registrada aqui en vez de disimularse.

Checks humanos que siguen SIN FIRMAR:

- **H-09 BIS** (estados sobre el diseno actual). Era el unico criterio marcado como
  NO APTO automatico. El diseno cambio tres veces desde la ultima firma.
- **H-10, H-11** (usuario ajeno, accesibilidad). En contradiccion desde el 14 de agosto.
- **H-12** (cortar la red a mitad de turno). Tiene equivalente automatico verificado.
- **H-14** (temperatura 0.1 frente a 1.5).
- **H-16** (leer el informe entero).
- **H-18** (instalar desde cero en otra maquina). Se verifico por aproximacion: el
  chequeo AST de imports contra `requirements.txt` no encuentra ninguna sin declarar,
  y `pip install --dry-run --ignore-installed -r requirements.txt` resuelve entero.
  **No es lo mismo que instalarlo de verdad en otra maquina.**
- **R-01** (regresion tras la Fase 2).

Firmados de hecho, aunque no marcados en su momento:

- **H-17** (video). Grabado y entregado.
- **H-19** (modo sin internet). La duena lo probo apagando el wifi el 2026-08-23, lo
  reprobo, se corrigio, y volvio a probarlo hasta darlo por bueno.

**Consecuencia practica:** si algo falla en la sustentacion en vivo, lo mas probable
es que sea uno de estos. El ensayo con la aplicacion abierta sigue siendo la mejor
inversion de tiempo antes de presentar.

## Current facts

- **Python 3.14.5**, venv en `.venv/`. 189 pruebas automaticas, todas en verde,
  en unos doce segundos y sin red.
- **Diez herramientas** por tool calling: calcular, hora, clima, estado del equipo,
  buscar web, abrir pagina, volumen, brillo, abrir carpeta, reproducir video.
- **Modo sin internet** (T-21): faster-whisper, Qwen2.5-0.5B y la voz de Windows.
  Los modelos se descargan con `python -m core.modo_local`, una vez y con conexion.
- **La asistente se llama Elena.** El proyecto se llama Mini-JARVIS.
- **Ninguna credencial versionada.** Verificado sobre el historial completo, no solo
  sobre el ultimo commit.

## Nota sobre las fechas

Este archivo estuvo fechado el 2026-08-23 diciendo "QUEDAN 4 DIAS" hasta el
2026-08-28, cinco dias despues de la fecha que anunciaba. Viajaba asi dentro del ZIP
y del repositorio entregados. Es la segunda vez en el proyecto que las fechas del
panel se desincronizan de la realidad; la primera fue un desfase de seis dias
detectado el 2026-08-23. **Si se retoma este proyecto, comprobar la fecha del sistema
antes de fiarse de cualquier fecha escrita en `.agents/`.**

## Blockers

Ninguno.
