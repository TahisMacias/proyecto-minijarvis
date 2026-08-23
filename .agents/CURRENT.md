# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-23 (sesion 4)
source_commit: (ver ultimo [STATE]; limpio)
assurance: Lean
active_plan: PLAN_v1.0-entrega-27ago.md
active_task: ninguna — sesion cerrada, Fase 2 bloqueada esperando el OK de la duena
last_verdict: auditoria de cierre de Fase 1 = NO APTO; los 3 defectos corregidos en
  72f1134 y publicados. Los 2 hallazgos que quedaban abiertos, cerrados en b215812.
  Fase 1 tecnicamente completa y sin deuda de auditoria pendiente.
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico)
deadline: 2026-08-27
```

## COMO RETOMAR EN UNA SESION NUEVA

Di "continua el plan". Todo el estado vive aqui, no en ninguna conversacion.
Orden de lectura: este archivo -> `PLAN_v1.0-entrega-27ago.md` -> `AGENTS.md`.
El diseno completo esta en `docs/specs/2026-08-13-mini-jarvis-design.md`.

## Next action

**FASE 2 COMPLETA.** Las cuatro tareas en APTO el 2026-08-23, ocho dias antes de su
fecha limite, y con los tres bloques que pidio la duena, no un subconjunto.

Lo que queda antes de la Fase 3 **es todo suyo**. Ningun agente puede firmarlo:

1. **H-15 — probar las herramientas por voz.** Empezar por *"cual es la raiz cuadrada
   de 3340"*, que es el fallo que origino la calculadora. Despues la bateria, una
   busqueda, y abrir Wikipedia. Por ultimo pedirle un sitio prohibido: debe negarse
   con palabras, sin abrir nada.
2. **H-09 BIS — volver a firmar los estados sobre la ventana nueva.** El tema cambio
   de claro a oscuro por completo; la firma del 14 de agosto era sobre la ventana
   pastel y no vale. Es el unico criterio del proyecto marcado como NO APTO
   automatico, asi que conviene mirarlo en serio.
3. **H-14 — mover los sliders** y comprobar que la diferencia se nota y se explica.
4. **Reprobar 2.3, 5.1 y 5.3** de `docs/pruebas-manuales.md`, que sigue pendiente
   desde la Fase 1.
5. **R-01 — regresion**: repetir H-06 y H-12 para comprobar que las herramientas y los
   controles nuevos no rompieron la conversacion basica ni el manejo de errores.

Despues, **Fase 3**: informe (T-16), video (T-17) y ensayo (T-18). Los dias 26 y 27
son intocables y no se escribe codigo de producto.

### Aviso sobre el calendario

Quedan 10 dias. La Fase 2 se hizo en uno, asi que el margen sigue intacto: el riesgo
que se advirtio al abrirla con alcance completo **no se materializo**. Ahora el camino
critico ya no es el codigo, es el informe y el video.

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
- **128 pruebas verdes en ~4 s**, sin red, sin microfono y sin gastar saldo.
- Codigo entregado: `config.py`, los seis modulos de `core/`, `gui/desktop_app.py`,
  `main.py`, `exploration/transformer_lab.py`, `Iniciar Mini-JARVIS.bat`.
- **`tools/` entregado (T-15)**: `calcular`, `estado_laptop`, `buscar_web` y
  `abrir_kiosk`. La calculadora **no usa `eval`**: analiza con `ast` contra lista
  blanca y evalua el arbol a mano. Verificado contra la API real: el modelo las pide
  por su cuenta.
- **Ventana rediseñada (T-19 + T-14)**: tema oscuro turquesa y rosa, tres columnas sin
  pestanas, mapa de atencion en superposicion, sliders, indicador de memoria, visor de
  system prompt y selector de modelo en caliente.
- **T-13 cerrada en APTO**: su contenido quedo absorbido por T-19. Ya no es una
  pestana; el laboratorio se ve a la vez que la conversacion.
- La extraccion de atencion sobre BETO exige `attn_implementation="eager"`; el
  laboratorio lo verifica en tiempo de ejecucion y falla con mensaje explicito si no.
- El enunciado en PDF **no esta versionado** a proposito: es material del docente y el
  repositorio es publico.

## Open findings

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
