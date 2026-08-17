# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-17 (sesion 4)
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

**FASE 2 ABIERTA CON ALCANCE COMPLETO (A + B + C), autorizado por la duena el
2026-08-17.** Se le advirtio que con 8 dias utiles el riesgo cae sobre el informe y el
video, no sobre el codigo. Lo reafirmo. Queda ejecutado entero y la advertencia no se
repite.

### Orden de ejecucion — CAMBIADO respecto al plan original, con motivo

El plan decia T-13, T-14, T-15. Ese orden **construye la misma cosa dos veces**: T-14
mete sliders, indicadores y selector de modelo en la ventana actual, y T-19 acto
seguido elimina las pestanas y redistribuye todo. Orden nuevo:

1. **T-15 — herramientas + calculadora.** Backend puro, no toca la ventana, asi que no
   compite con nada. Es ademas lo de mayor peso en la rubrica (Tool Calling es
   requisito) y lo que arregla un fallo que la duena vio con sus ojos.
2. **T-19 + T-14 juntas.** Se disena la ventana nueva **ya con** los controles de
   sustentacion dentro, en vez de ponerlos y moverlos. Sin pestanas, con el modulo de
   estado grande y el mapa de atencion en superposicion.
3. **T-13 queda absorbida por T-19**: su contenido pasa a verse junto a la
   conversacion. Su veredicto en suspenso se resuelve ahi.

### Restriccion de derechos del bloque B, ya resuelta por la via segura

El repositorio es publico y el personaje es propiedad de Crypton Future Media. **No se
sube arte de terceros.** Se hace arte original generado por codigo con esa estetica
(turquesa `#39C5BB` y rosa). Si la duena consigue una imagen cuyos derechos tenga, se
sustituye en un commit de una linea.

### Sigue pendiente de la duena, en paralelo

- **Reprobar 2.3, 5.1 y 5.3** de `docs/pruebas-manuales.md`.
- **Decir si H-10 y H-11 estan hechos.**

## Fase 2 propuesta — pedida por la duena, NO empezada

Tres bloques nuevos que se suman a lo ya planificado. Ninguno se ha tocado.

### A. Tool calling con calculadora (amplia T-15)
- La duena probo "raiz cuadrada de 3340" y el modelo respondio "no tengo calculadora
  pero puedo dar una respuesta aproximada". Un LLM **no calcula: predice texto**.
- Se anade `calcular` como cuarta herramienta. No hace falta ningun servicio externo:
  Python es la calculadora. **Nunca con `eval` sobre lo que diga el modelo**; hay que
  analizar la expresion con `ast` y una lista blanca de operaciones y funciones.
- Valor doble: arregla el sintoma y da una demostracion muy clara del antes y despues.

### B. Rediseno visual con tematica Hatsune Miku
- Paleta del personaje (turquesa `#39C5BB` y rosa) y un fondo con el personaje.
- **Punto abierto de derechos**: el repositorio es publico y el diseno del personaje es
  propiedad de Crypton Future Media. No conviene subir arte de terceros. Alternativas:
  arte original generado por codigo con esa estetica, o que la duena aporte una imagen
  cuyos derechos tenga. Hay que decidirlo antes de implementar.
- Voz "tipo Miku": no existe un TTS libre con esa voz. Lo viable es subir tono y ritmo
  de una voz de edge-tts; ya esta preparado en `config.py` (`TONO_TTS`, `RITMO_TTS`),
  sin aplicar todavia en el motor de voz.

### C. Nueva distribucion de la ventana
- Modulo de estado mas grande.
- **Quitar las pestanas**: conversacion y laboratorio visibles a la vez, para que la
  presentacion sea mas vistosa.
- El mapa de atencion pasa a ser un boton que lo abre **expandido sobre la ventana**,
  con boton de cerrar visible.

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
- **70 pruebas verdes en ~4 s**, sin red, sin microfono y sin gastar saldo.
- Codigo entregado: `config.py`, los seis modulos de `core/`, `gui/desktop_app.py`,
  `main.py`, `exploration/transformer_lab.py`, `Iniciar Mini-JARVIS.bat`.
- Falta `tools/` (T-15). El orquestador ya lo soporta: recibe `ejecutar_herramienta` y
  respeta el limite de 2 rondas; sin ese argumento responde con el texto disponible.
- **T-13 (pestana Laboratorio) esta construida y verificada**, pero se hizo antes de
  que la duena pidiera detener la Fase 2. Su veredicto queda en suspenso. Si el
  rediseno de la ventana sigue adelante, esa pestana desaparece como tal.
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
- ~~`Sintesis del proyecto.md` contradice decisiones vigentes.~~ **CERRADO**
  (2026-08-17, commit `b215812`). Lleva un aviso de documento superado con la tabla de
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
- ~~**Lo que se importa se declara.**~~ **CERRADO CON EVIDENCIA** (2026-08-17, commit
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
