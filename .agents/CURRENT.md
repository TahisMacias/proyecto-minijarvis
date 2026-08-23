# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-23 (sesion 5, cierre)
source_commit: (ver ultimo [STATE]; limpio y sincronizado con origin/main)
assurance: Lean
active_plan: PLAN_v1.0-entrega-27ago.md
active_task: ninguna — no queda trabajo de codigo pendiente
last_verdict: enunciado repasado ENTERO y cerrado. Los 7 requisitos obligatorios, los
  5 tecnicos, los 5 eticos y las 6 preguntas guia, cubiertos.
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico)
deadline: 2026-08-27  (QUEDAN 4 DIAS)
```

## COMO RETOMAR EN UNA SESION NUEVA

Di "continua el plan". Todo el estado vive aqui, no en ninguna conversacion.
Orden de lectura: este archivo -> `PLAN_v1.0-entrega-27ago.md` -> `AGENTS.md`.
El diseno completo esta en `docs/specs/2026-08-13-mini-jarvis-design.md`.

## Next action

**NO QUEDA TRABAJO DE CODIGO.** El repaso completo del enunciado esta cerrado. Todo lo
que falta es de la duena y ninguna parte se puede automatizar.

### Lo unico que de verdad importa ahora

1. **GRABAR EL VIDEO.** Es el mayor riesgo abierto del proyecto. El guion esta escrito
   y probado en `docs/guion-video.md`: bloques por minuto, lo que dice entre comillas
   para leerlo tal cual, y las frases a Elena ya verificadas. Ella dijo el 2026-08-23
   que lo grabaria al dia siguiente.
2. **Ensayar la sustentacion** con `docs/guion-mapa-atencion.md`, que ya trae
   preparadas las respuestas a las seis preguntas guia de la seccion 12.

### Checks humanos que siguen pendientes

- **H-07 (la voz).** Firmado el 14 con Dalia. Desde entonces la voz cambio dos veces y
  hoy es `es-AR-ElenaNeural`. La firma no se hereda: hay que volver a oirla en la app.
- **H-09 (los estados).** Firmado el 14 sobre la ventana pastel. Ha habido TRES disenos
  desde entonces. Hay que volver a mirarlo sobre el diseno actual. Es el unico criterio
  del proyecto marcado como NO APTO automatico.
- **H-10 y H-11**: siguen en contradiccion desde la auditoria del 14. Solo ella puede
  decir si se hicieron. Ver `TESTING.md`.
- **Prueba 5.3** de `docs/pruebas-manuales.md`: apagar el wifi y ver el triangulo
  ambar. Ya lo hizo de facto probando el modo sin internet, pero sin marcarlo.

### Antes de la entrega

- Verificar saldo en Together AI la vispera (26 ago).
- Correr `python -m core.modo_local` si alguna vez se limpia la cache: sin esos modelos
  descargados, el modo sin internet tarda un minuto en vez de cuatro segundos.

## Blockers

- Ninguno tecnico. El unico freno es deliberado: falta el OK de la duena.

## Current facts

- **Entrega: 27 de agosto de 2026.** Fase 1 cerrada el 14 de agosto, con 8 dias de
  margen sobre su fecha limite.
- **La aplicacion funciona de extremo a extremo con voz real**, verificado por la
  duena: hablar -> transcribir -> responder -> voz, con memoria entre turnos.
- Repositorio publico en `https://github.com/TahisMacias/proyecto-minijarvis`,
  local y remoto sincronizados.
- **Modelos (probados uno por uno contra la API, no por el listado)**:
  predeterminado `Qwen/Qwen3.8-2.4T-A95B` (razonamiento, 1-4 s por respuesta),
  alterno `Qwen/Qwen2.5-7B-Instruct-Turbo`, STT `openai/whisper-large-v3`.
  **Aparecer en `GET /v1/models` no prueba disponibilidad**: casi todos los modelos
  grandes devuelven HTTP 400 "non-serverless". Precios anotados en `config.py`.
- Python 3.14.5, entorno en `.venv/`, **14 dependencias** fijadas en
  `requirements.txt`. La numero 14 es `pillow==12.3.0`, anadida en la auditoria del
  2026-08-14: `gui/desktop_app.py` la importa directamente y no estaba declarada; se
  instalaba de rebote porque matplotlib depende de ella.
  Instalacion desde cero verificada en un entorno limpio **antes** de ese cambio; la
  verificacion con el `requirements.txt` nuevo queda para T-18.
- **171 pruebas verdes en ~12 s**, sin red, sin microfono y sin gastar saldo.
- Codigo entregado: `config.py`, los seis modulos de `core/`, `gui/desktop_app.py`,
  `main.py`, `exploration/transformer_lab.py`, `Iniciar Mini-JARVIS.bat`.
- **`tools/` entregado (T-15)**: SEIS herramientas — `calcular`, `clima`, `hora`,
  `estado_laptop`, `buscar_web` y `abrir_pagina`. La calculadora **no usa `eval`**: analiza con `ast` contra lista
  blanca y evalua el arbol a mano. Verificado contra la API real: el modelo las pide
  por su cuenta.
- **Ventana en su TERCER diseno (T-20 "neon minimo")**, elegido por la duena entre
  tres bocetos dibujados. Sin cajas, dos columnas, el reactor a la izquierda.
- **La asistente se llama Elena** y responde a su nombre. El proyecto sigue siendo
  Mini-JARVIS. El nombre vive en `config.NOMBRE_ASISTENTE`, un solo sitio.
- **Modo sin internet (T-21)**: oye con faster-whisper, piensa con Qwen2.5-0.5B y habla
  con la voz de Windows, todo en local. Cambia solo al caerse la red y lo avisa. Los
  modelos se precalientan al arrancar; sin eso el primer turno tardaba mas de un minuto
  y ahora tarda cuatro segundos.
- **T-13 cerrada en APTO**: su contenido quedo absorbido por T-19. Ya no es una
  pestana; el laboratorio se ve a la vez que la conversacion.
- La extraccion de atencion sobre BETO exige `attn_implementation="eager"`; el
  laboratorio lo verifica en tiempo de ejecucion y falla con mensaje explicito si no.
- El enunciado en PDF **no esta versionado** a proposito: es material del docente y el
  repositorio es publico. **Vive en la raiz local y en Descargas.** SE LEYO ENTERO el
  2026-08-23; hasta entonces el proyecto trabajaba contra el resumen de APPCORE.md.

## Open findings

- **EL HALLAZGO DE LA SEMANA: nadie habia leido el enunciado entero.** El proyecto
  trabajaba contra `APPCORE.md`, un resumen escrito en la primera sesion. El PDF estaba
  en la carpeta local todo el tiempo, y el propio `INDEX.md` lo declaraba "maxima
  autoridad academica". Leerlo el 2026-08-23 encontro, en una sola pasada: que faltaba
  **positional encoding**, que lo pide dos veces y cae en el criterio del 25 %; que la
  rubrica premia una **interfaz tipo HUD** que refuerce la identidad Jarvis, cuando el
  diseno se estaba haciendo contra descripciones sueltas de la duena; que **el clima y
  la hora** estaban en la lista de funciones reales; y dos huecos teoricos.
  **Regla que sale de aqui: leer la fuente antes de trabajar contra un resumen de la
  fuente.** Es la misma leccion que el proyecto ya tenia escrita para los modelos de la
  API -"que algo aparezca en un listado no prueba nada"- aplicada al sitio donde mas
  dolia.
- **Describir un diseno con palabras no funciona.** Dos intentos fallidos -tematica
  Miku, luego HUD- disenados a partir de descripciones. El tercero se acerto dibujando
  tres bocetos y dejando que eligiera mirando. Lo mismo con la voz: ocho muestras y
  eligio de oido. **Cuando el criterio es perceptual, hay que ensenar, no describir.**

- **Un color que el usuario no puede nombrar no comunica nada.** Los tres defectos que
  encontro la duena viven en la frontera entre el codigo y la percepcion: ninguna
  prueba automatica los habria visto. Conviene seguir alternando pruebas y uso real.
- El nivel Ingeniero de la jerarquia de tres niveles quedo sin segunda observacion: las
  ultimas sesiones no lo usaron. El criterio escrito sigue vigente por si se retoma.
- **El entregable de mayor peso de la rubrica no se explicaba solo.** El 2026-08-23 la
  duena miro el mapa de atencion y dijo que no entendia que mostraba ni que significaba
  "capa 6 de 12, cabeza 4 de 12". El grafico es correcto y esta bien etiquetado; el
  problema es que **estaba escrito para alguien que ya sabe lo que esta mirando**. Vale
  el 25 % de la nota y quien lo tiene que defender en voz alta no es programadora.
  Se escribio `docs/guion-mapa-atencion.md`. **Leccion general: un entregable que solo
  se entiende con quien lo hizo al lado no esta terminado.** Aplica igual al informe
  (T-16) y al video (T-17): el criterio no es que sean correctos, es que ella pueda
  defenderlos sola.
- ~~`Sintesis del proyecto.md` contradice decisiones vigentes.~~ **CERRADO**
  (2026-08-23, commit `b215812`). Lleva un aviso de documento superado con la tabla de
  las cinco contradicciones: los dos modelos inservibles, `asyncio`, las 7 herramientas
  que son 3, el color de PENSANDO y la carpeta raiz `mini_jarvis/` que nunca existio.
  No se borro: la distancia entre lo planeado y lo posible es material de sustentacion.
- **La documentacion se desincroniza en silencio; el codigo no.** Los tres defectos de
  la auditoria eran afirmaciones falsas, no fallos de ejecucion: ninguna prueba, ningun
  gate y ningun uso real los habria detectado nunca, porque la aplicacion funciona
  perfectamente mientras el README miente. El defecto entro cuando un commit cambio
  `config.py` y dejo el README como estaba. **Regla que sale de aqui:** todo cambio de
  un identificador de modelo, de una version fijada o de un precio obliga a revisar
  `README.md` y `docs/specs/` en el mismo commit.
- ~~**Lo que se importa se declara.**~~ **CERRADO CON EVIDENCIA** (2026-08-23, commit
  `b215812`). Se recorrio el AST de los 19 archivos `.py` y se mapeo cada import a su
  distribucion: **los 11 de terceros estan declarados**. Pillow era el unico hueco.
  El barrido inverso encontro tres pines que nadie importa —`psutil`,
  `duckduckgo-search` (T-15) y `tiktoken` (T-14)— y que el comentario de `tiktoken`
  era **falso**: decia servir al indicador de memoria, y `core/memory.py` no usa
  ningun tokenizador a proposito. Comentarios corregidos; ninguna dependencia borrada,
  porque eso es decision de alcance de la duena.

## Human actions

- [x] Autenticacion con GitHub, `TOGETHER_API_KEY` validada, proveedor de STT decidido.
- [x] **Recorrido completo de `docs/pruebas-manuales.md`** (2026-08-14). Todo el lado
      tecnico paso; los tres fallos reportados estan corregidos y publicados.
- [x] **Push autorizado y hecho** (2026-08-14). Local y remoto sincronizados.
- [ ] **Reprobar 5.1, 5.3 y 2.3** con las correcciones ya aplicadas. Es la mas urgente:
      hasta hacerla, las tres correcciones del uso real no tienen evidencia.
- [ ] **Decir si H-10 y H-11 ya estan hechos.** En `docs/pruebas-manuales.md` las
      pruebas 8.2, 8.3 y 9.1 estan marcadas `[X]`; en `TESTING.md` figuran pendientes.
      No se firmaron en su nombre. H-10 (una persona ajena usa la app sin
      instrucciones) es de los pocos que no se pueden improvisar el mismo dia.
- [ ] Verificar saldo en Together AI la vispera de la sustentacion (26 ago).
- [ ] No reactivar OneDrive durante el proyecto.
- [ ] Reservar los dias 26 y 27 para informe, video y ensayo. Sin codigo.
