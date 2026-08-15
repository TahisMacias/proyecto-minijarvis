# CURRENT - Mini-JARVIS

```yaml
updated_at: 2026-08-14 (sesion 3, cierre)
source_commit: (ver ultimo [STATE]; limpio, pendiente de push a origin/main)
assurance: Lean
active_plan: PLAN_v1.0-entrega-27ago.md
active_task: ninguna — sesion cerrada, Fase 2 bloqueada esperando el OK de la duena
last_verdict: auditoria de cierre de Fase 1 = NO APTO; los 3 defectos corregidos en
  el commit 72f1134. Fase 1 tecnicamente completa.
backup: remote origin -> https://github.com/TahisMacias/proyecto-minijarvis (publico)
deadline: 2026-08-27
```

## COMO RETOMAR EN UNA SESION NUEVA

Di "continua el plan". Todo el estado vive aqui, no en ninguna conversacion.
Orden de lectura: este archivo -> `PLAN_v1.0-entrega-27ago.md` -> `AGENTS.md`.
El diseno completo esta en `docs/specs/2026-08-13-mini-jarvis-design.md`.

## Next action

**BLOQUEADO A PROPOSITO. No abrir la Fase 2 sin el OK explicito de la duena.**

La auditoria que pidio **ya se hizo** (2026-08-14, ver el plan). Lo que queda antes
de reanudar, en este orden:

1. **Push pendiente**: los commits `72f1134` y el `[STATE]` de este cierre estan solo
   en local. Preguntarle antes de publicarlos: el repositorio es publico.
2. **Reprobar las pruebas 2.3, 5.1 y 5.3** de `docs/pruebas-manuales.md` con las
   correcciones ya aplicadas. Sin esto no hay evidencia de que funcionen en uso real.
3. **Resolver H-10 y H-11**: figuran firmados en el recorrido manual y pendientes en
   `TESTING.md`. Solo ella puede decir cual es cierto.
4. Con su OK, abrir la **Fase 2 con alcance ampliado** (ver la seccion siguiente).

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
- `Sintesis del proyecto.md` sigue en el repositorio como documento historico y ya
  contradice varias decisiones vigentes (`asyncio`, 7 herramientas, modelos). Conviene
  marcarlo como superado antes de la entrega. **Sigue abierto**: la auditoria del
  2026-08-14 puso el aviso equivalente en `docs/specs/`, que es el que alimenta el
  informe, pero no toco este archivo por estar fuera del alcance autorizado.
- **La documentacion se desincroniza en silencio; el codigo no.** Los tres defectos de
  la auditoria eran afirmaciones falsas, no fallos de ejecucion: ninguna prueba, ningun
  gate y ningun uso real los habria detectado nunca, porque la aplicacion funciona
  perfectamente mientras el README miente. El defecto entro cuando un commit cambio
  `config.py` y dejo el README como estaba. **Regla que sale de aqui:** todo cambio de
  un identificador de modelo, de una version fijada o de un precio obliga a revisar
  `README.md` y `docs/specs/` en el mismo commit.
- **Lo que se importa se declara.** Pillow funcionaba de rebote. Antes de T-18 conviene
  revisar si algun otro `import` del proyecto depende de una dependencia que nadie
  pidio explicitamente.

## Human actions

- [x] Autenticacion con GitHub, `TOGETHER_API_KEY` validada, proveedor de STT decidido.
- [x] **Recorrido completo de `docs/pruebas-manuales.md`** (2026-08-14). Todo el lado
      tecnico paso; los tres fallos reportados estan corregidos y publicados.
- [ ] **Autorizar el push** de `72f1134` y del `[STATE]` de este cierre. El
      repositorio es publico, asi que no se publica sin su OK.
- [ ] **Reprobar 5.1, 5.3 y 2.3** con las correcciones ya aplicadas. Es la mas urgente:
      hasta hacerla, las tres correcciones del uso real no tienen evidencia.
- [ ] **Decir si H-10 y H-11 ya estan hechos.** En `docs/pruebas-manuales.md` las
      pruebas 8.2, 8.3 y 9.1 estan marcadas `[X]`; en `TESTING.md` figuran pendientes.
      No se firmaron en su nombre. H-10 (una persona ajena usa la app sin
      instrucciones) es de los pocos que no se pueden improvisar el mismo dia.
- [ ] Verificar saldo en Together AI la vispera de la sustentacion (26 ago).
- [ ] No reactivar OneDrive durante el proyecto.
- [ ] Reservar los dias 26 y 27 para informe, video y ensayo. Sin codigo.
