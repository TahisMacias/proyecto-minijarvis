# CONTEXT - registro cronologico

Operacion normal es append-only. Las entradas nuevas van al final.
Solo un MAINTAIN o COMPACT explicito puede resumir entradas viejas, y debe preservar
fechas, decisiones, riesgos abiertos, referencias a tareas/commits y un puntero al archivo.

## 2026-08-13 - Jornada 1, resumida (texto completo en `archive/CONTEXT_2026-08-13.md`)

Seis entradas compactadas el 2026-08-14. Lo que hay que recordar:

- **INIT** del workflow y perfil de aseguramiento **Lean**. Roles: Obrero implementa,
  Ingeniero audita, Arquitecto cierra fase y publica.
- **Diseno aprobado** (`docs/specs/2026-08-13-mini-jarvis-design.md`, 17 secciones).
  Dos desviaciones deliberadas de la sintesis original del equipo, con motivo escrito:
  **nada de `asyncio` persistente** (Tkinter obliga a `mainloop` en el hilo principal;
  dos modelos de concurrencia conviviendo es donde un equipo novato pierde dias) y
  **3 herramientas en vez de 7**.
- **Plan v1.0**: 18 tareas, 3 fases, entrega el 27 de agosto.
- **T-01 (spike de entorno) APTO**: Python 3.14.5 confirmado, todo el stack con wheels
  `cp314`. Hallazgo critico que se arrastra a todo el proyecto: `transformers 5.x` usa
  SDPA por defecto y **devuelve `None` en `output_attentions` sin lanzar error**; hay
  que cargar con `attn_implementation="eager"`.
- **T-02 (esqueleto) APTO**. Se declaro excepcion al saltar el nivel Ingeniero.
- **Correccion de diseno de la paleta**: la seccion 11 del spec no asignaba color a
  RESPONDIENDO ni a ATENCION y dos estados quedaban compartiendo rosa. **Lo detecto el
  Obrero**, el nivel mas bajo de la jerarquia, revisando fuera de su alcance. Se anadio
  durazno para ATENCION y una columna de forma por estado. Argumento a favor de pedir
  a los Obreros que reporten inconsistencias del diseno aunque no les toque.
- **T-03 (config.py) APTO**: credenciales desde `.env`, validacion al importar, ningun
  mensaje de error interpola la clave.

## 2026-08-14 - T-11 cerrada: existia, pero no estaba entregada

- Changed: `exploration/transformer_lab.py`, `README.md`,
  `docs/evidencia/T-11-salida-transformer_lab.txt` (commit `f1a9f43`).
- **Defecto de proceso encontrado al retomar:** CURRENT afirmaba que T-11 no se habia
  hecho y que el archivo no existia. `git show --stat 6d0cf88` demostro lo contrario:
  las 508 lineas del laboratorio y el PNG habian entrado dentro del commit de T-03,
  sin veredicto propio y sin gate ejecutado. Un archivo puede existir y aun asi no
  estar cerrado; y un commit puede arrastrar trabajo de otra tarea sin que nadie lo
  note. Regla derivada: antes de declarar que una tarea no se hizo, mirar el diff de
  los commits recientes, no solo el estado del arbol.
- Veredicto T-11: **APTO**. Verificacion ejecutada, no aceptada por reporte:
  `python -m exploration.transformer_lab` -> exit 0; 12 capas de atencion de
  `(1, 12, 20, 20)`; embeddings `(1, 20, 768)`; fila de atencion = `1.000000`;
  PNG regenerado identico byte a byte (89415 bytes); `compileall` exit 0.
  El mapa se inspecciono visualmente: la franja iluminada a la izquierda de la
  diagonal confirma que la capa 6 / cabeza 4 es una cabeza de token anterior, tal
  como el codigo afirma. La afirmacion del script y la imagen concuerdan.
- Dos correcciones aplicadas por el Arquitecto sobre el product plane, **declaradas
  como excepcion** (mismo criterio que en T-03):
  - La salida del nivel 1 mostraba tokens como `ÃŃa` sin explicarlos. No es un error:
    el tokenizador de Qwen es byte-level BPE y opera sobre bytes UTF-8. Pero esa
    salida se proyecta en la sustentacion, y sin explicacion parece un programa roto
    delante del tribunal. Se anadio un aviso que convierte el detalle en argumento.
  - `README.md` afirmaba que el laboratorio no estaba implementado. Era falso, y el
    repositorio es publico.
- Barrido de estado obsoleto en el plan: T-03 seguia como `ready` estando APTO, y
  T-04, T-05 y T-08 seguian `blocked (T-03)`. Corregido.
- Unresolved: la observacion sobre el nivel Ingeniero sigue abierta. En esta sesion
  no hubo despacho jerarquico, asi que no aporta evidencia ni a favor ni en contra.
- Next: push, y despachar T-04 (T-05 y T-08 pueden ir en paralelo, no comparten archivos).

## 2026-08-14 - Cinco modulos de core/ entregados, y un hallazgo que salva la demo

- Changed: `core/memory.py`, `core/audio_capture.py`, `core/stt_client.py`,
  `core/llm_engine.py`, `core/tts_engine.py`, `tests/`, `pytest.ini`,
  `requirements.txt`, `config.py`, `exploration/transformer_lab.py`.
  Commits `04f2fbc`, `f7230a7`, `ba169e1`, `5874a35`, `b620ac7`, `38715f7`, `a034533`.
- Ejecutado por el Arquitecto, **excepcion declarada** al reparto de roles: la duena
  pidio continuar con todo en una sola sesion. Cada tarea llevo su gate ejecutado, no
  reportado, y su commit propio. La separacion que si se mantuvo es la que importa:
  ninguna tarea se dio por buena sin evidencia reproducible.
- **HALLAZGO MAYOR (T-07): los dos modelos del plan no los sirve esta cuenta.**
  `Qwen/Qwen2.5-72B-Instruct` y `meta-llama/Llama-3.3-70B-Instruct` figuran en
  `GET /v1/models` —que es como se dieron por verificados el 2026-08-13— pero
  responden HTTP 400 "Unable to access non-serverless model". Estan en el catalogo de
  Together, no en su servicio compartido; usarlos exigiria pagar un endpoint dedicado.
  Se probaron catorce identificadores uno por uno hasta encontrar los que responden:
  `meta-llama/Llama-3.3-70B-Instruct-Turbo` y `Qwen/Qwen2.5-7B-Instruct-Turbo`.
  **Leccion general, aplicable mas alla de este proyecto: que un recurso aparezca en
  un listado no prueba que se pueda usar. Solo lo prueba ejercerlo.** De no haberse
  detectado ahora, habria aparecido como un 400 sin explicacion el dia de la demo.
- Consecuencia en cadena: el nivel 1 del laboratorio decia usar "el tokenizador del
  LLM de produccion" nombrando un modelo inaccesible. Se repunto al de
  `Qwen/Qwen2.5-7B-Instruct`, que es el del modelo alterno real. No se uso el de
  Llama porque su repositorio en Hugging Face esta restringido: se comprobo y
  devuelve "You are trying to access a gated repo". Una demostracion que depende de
  un permiso ajeno es fragil.
- Decisiones de implementacion que se apartan de lo previsto, con motivo:
  - `core/memory.py` **no importa `config.py`**, siguiendo la tabla de modulos del
    diseno, que lo lista sin dependencias. Efecto util: las pruebas corren en una
    maquina sin `.env` ni credenciales.
  - La reproduccion de voz usa **MCI** de Windows via `ctypes` en vez de anadir una
    libreria de audio: edge-tts devuelve MP3 y Windows ya sabe decodificarlo.
  - Se anadio `pytest` (no estaba en `requirements.txt` pese a que tres gates del
    plan lo exigen) y `pytest.ini` con `pythonpath = .`.
- Verificaciones que no se aceptaron por reporte: transcripcion real de audio
  sintetizado, reproduccion medida en 4.92 s para confirmar que bloquea, captura real
  de microfono releida con el modulo `wave`, y cambio de modelo en caliente con la
  conversacion viva.
- Unresolved: H-04 y H-07 pendientes de la duena (son de oido, nadie mas los puede
  hacer). El nivel Ingeniero sigue sin segunda observacion: esta sesion no uso
  jerarquia, asi que no aporta evidencia.
- Next: T-09, el orquestador. Es la tarea de mayor riesgo tecnico del plan.

## 2026-08-14 - Fase 1 completa: la aplicacion habla, escucha y responde

- Changed: `core/orchestrator.py`, `gui/desktop_app.py`, `main.py`, `README.md`,
  `tests/test_orchestrator.py`, `tests/test_paleta_estados.py`, evidencia.
  Commits `c351170` (T-09), `d51cbf5` (T-10) y el de T-12.
- **T-09, la tarea de mayor riesgo del plan, cerrada sin sobresaltos.** La regla de
  "ningun hilo toca un widget" no se dejo a la disciplina: el orquestador simplemente
  no tiene acceso a la GUI, y una prueba lee su AST para que siga siendo cierto. Es
  la diferencia entre una regla escrita y una regla que se cumple sola.
- **Tres defectos reales que solo aparecen al ejecutar, no al leer:**
  1. Una transcripcion de puros espacios pasaba como texto valido (la encontro una
     prueba de frontera).
  2. Con el escalado de Windows al 133 %, la ventana de 680 se dibujaba de 850 px y
     **el boton de hablar quedaba debajo de la barra de tareas**. La aplicacion habria
     parecido rota el dia de la demostracion sin estarlo. Ahora la altura se calcula
     contra la pantalla real.
  3. Al auditar los 7 fallos de la seccion 13 para T-12 faltaba uno: el **reintento
     unico** ante respuesta vacia del LLM. Estaba en el diseno y no en el codigo.
     Auditar contra la lista escrita, y no contra el recuerdo, es lo que lo encontro.
- Verificacion de red que no se simulo: se apunto el motor a un puerto cerrado para
  provocar un fallo de conexion **real** a mitad de turno. La aplicacion aviso con
  lenguaje llano, volvio a REPOSO y siguio utilizable.
- H-09 se verifico midiendo, no a ojo: se instrumento el lienzo y se comprobo que los
  cuatro estados activos usan cuatro colores y cuatro figuras distintas. Queda una
  prueba que falla si dos estados llegaran a compartir color: ese defecto ya ocurrio
  una vez en este proyecto y no deberia poder repetirse en silencio.
- Unresolved: H-04, H-07, H-09, H-10 y H-12 son de la duena (oido, vista y uso).
  Nadie mas los puede firmar.
- Next: cierre de la Fase 1 y decision sobre la Fase 2 (T-13 a T-15).

## 2026-08-14 - Cierre de la Fase 1

- La Fase 1 completa (T-01 a T-12) queda en APTO el 2026-08-14, ocho dias antes de su
  fecha limite del 22 de agosto. El 65 % de la rubrica que protege esta fase esta
  cubierto, y tambien el 25 % del laboratorio del Transformer.
- Nota de proceso: el commit de T-12 mezclo el plano de producto y el de control en
  un solo commit. Es una desviacion menor de la regla de dos planos; se deja anotada
  aqui en vez de reescribir el historial de un repositorio ya publicado.
- **La Fase 2 no arranca todavia, y es a proposito.** El plan dice que no empieza
  hasta que la Fase 1 este *completa y verificada*, y lo que falta para verificada son
  cinco checks humanos (H-04, H-07, H-09, H-10, H-12) mas H-11. Son de oido, de vista
  y de uso: ninguna prueba automatica los sustituye, y firmarlos por cuenta propia
  seria justo el tipo de atajo que este workflow existe para evitar.
- Decision ya tomada y escrita: como la fase cerro con margen, la Fase 2 entra
  completa (T-13 pestana Laboratorio, T-14 controles de sustentacion, T-15 tool
  calling). No se recorta.

## 2026-08-14 - Testeo manual de la duena: tres defectos que el codigo no confesaba

- Changed: `config.py`, `core/audio_capture.py`, `core/orchestrator.py`,
  `gui/desktop_app.py`, `tests/`, `docs/pruebas-manuales.md`, lanzador `.bat`.
  Commits `8f29fab`, `252e4e4`, `ecedb64`, `88ac9b4`, `d688954`.
- La duena recorrio la lista de pruebas manuales completa. **Todo el lado tecnico
  paso**, con tres excepciones que ninguna prueba automatica habia detectado porque
  las tres viven en la frontera entre el codigo y la percepcion de una persona:
  1. **Whisper alucina con el silencio.** Pulsar y soltar sin hablar hacia que el
     asistente contestara a "gracias": ante audio vacio el modelo no devuelve cadena
     vacia, devuelve una muletilla de su entrenamiento. Se rechaza la grabacion antes
     de enviarla (duracion minima y volumen medio minimo).
  2. **El estado ATENCION existia pero nadie lo veia.** Se emitia ATENCION y REPOSO en
     la misma linea: el estado duraba microsegundos. La maquina de estados era
     correcta y el aviso era invisible. Ahora se queda 2.5 s, con temporizador y no
     con espera bloqueante, porque `_fallar` tambien corre en el hilo de la interfaz.
  3. **El verde menta se veia azul.** Los tintes Material 50 son casi blancos: como
     decoracion funcionan, como senal no. Se anadio un borde saturado por estado.
     **Leccion: un color que el usuario no puede nombrar no esta comunicando nada**, y
     eso no lo puede detectar ninguna prueba automatica de la paleta.
- **La barra espaciadora no servia para hablar** (reportado antes del recorrido). La
  repeticion automatica de teclas de Windows llega como parejas soltar+presionar, y
  ese "soltar" falso cerraba el microfono a los milisegundos. Corregido con
  antirrebote de 60 ms, `bind_all` y foco forzado al abrir.
- **Cambio de modelo pedido por la duena**: nada de Llama. No existe Qwen3.8 de 27B en
  Together y casi todos los grandes son "non-serverless"; de 26 identificadores
  probados uno por uno, el unico Qwen3.8 que responde es `Qwen3.8-2.4T-A95B`, un
  modelo de razonamiento que contesta en 1-4 s. Queda de predeterminado.
- **Nota de proceso, para no repetirla**: un commit se hizo con una prueba en rojo
  porque `pytest | tail` devuelve el codigo de salida de `tail`. La prueba estaba mal
  escrita, no el codigo, pero el gate no debio darse por bueno. Verificar el codigo de
  salida sin tuberia de por medio.
- Trabajo entregado fuera del plan, a peticion de la duena: lanzador
  `Iniciar Mini-JARVIS.bat` y `docs/pruebas-manuales.md`.
- **T-13 (pestana Laboratorio) se construyo antes de que la duena pidiera detener la
  Fase 2.** Esta entregada y verificada, pero su veredicto queda en suspenso hasta que
  ella de el OK: el plan dice que la Fase 2 no empieza sin la Fase 1 verificada.
- Next: **auditoria externa con otro agente**, y despues el OK de la duena para abrir
  la Fase 2 con el alcance nuevo (ver CURRENT > Fase 2 propuesta).
