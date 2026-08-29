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

## 2026-08-14 - Auditoria de cierre de la Fase 1: el codigo aguanto, la documentacion no

- Changed: `README.md`, `requirements.txt`, `docs/specs/2026-08-13-mini-jarvis-design.md`
  (commit `72f1134`); `.agents/` completo (este `[STATE]`).
- Auditoria que pidio la duena antes de autorizar la Fase 2. Alcance real leido, no
  hojeado: `config.py`, los seis modulos de `core/`, `gui/desktop_app.py`, `main.py`,
  `exploration/transformer_lab.py`, los cinco archivos de `tests/`, README, `.gitignore`
  y la coherencia interna de `.agents/`.
- **Veredicto: NO APTO.** Tres defectos, y el hallazgo de fondo es que **los tres eran
  afirmaciones falsas, no fallos de ejecucion**:
  1. El README declaraba `meta-llama/Llama-3.3-70B-Instruct-Turbo` como modelo
     predeterminado. El commit `88ac9b4` cambio `config.py` a Qwen3.8 y no toco el
     README. Rastreado con `git show --stat`: ocho archivos modificados, ninguno el
     README. Consecuencia real: la cita de modelos es un criterio de la rubrica, el
     repositorio es publico, y el informe tecnico (T-16) se iba a escribir desde
     `docs/specs/`, que citaba **tres** modelos que esta cuenta no puede usar.
  2. `Pillow` no estaba en `requirements.txt` pese a que `gui/desktop_app.py` hace
     `from PIL import Image`. Se instalaba de rebote: `pip show pillow` da
     `Required-by: matplotlib`, no customtkinter. Version suelta, y H-18 exige instalar
     en otra maquina siguiendo solo el README.
  3. Precio del STT diez veces inflado ($0.015 en vez de $0.0015 por minuto) en el
     README y en el documento de diseno.
- **Por que esto importa mas que un defecto de codigo**: ninguna prueba, ningun gate y
  ningun uso real los habria detectado jamas. La aplicacion funciona perfectamente
  mientras el README miente. Los gates verifican que el codigo haga lo que hace; nada
  verificaba que la documentacion dijera lo que el codigo hace. **Regla nueva en
  CURRENT > Open findings:** cambiar un identificador de modelo, una version fijada o
  un precio obliga a revisar `README.md` y `docs/specs/` en el mismo commit.
- Verificado de forma independiente, ejecutado y no reportado: 70 pruebas verdes en
  4.75 s; `compileall` exit 0; `.env` nunca aparece en el historial; barrido de
  patrones de secreto sobre **todos** los commits (`git rev-list --all`), limpio.
- Lo que la auditoria confirmo solido, y conviene no tocar: la cobertura de los 7
  fallos previstos, con una tabla que declara de frente lo que **no** cubre; la
  separacion de hilos, que se cumple por construccion — el orquestador no tiene un
  solo widget a mano — y no por disciplina; y una suite que verifica invariantes de
  verdad (una lee el AST del orquestador y falla si aparece un import de la GUI, otra
  falla si dos estados llegaran a compartir color).
- **Cuatro incoherencias del control plane**, reparadas aqui: el comando del gate en
  `AGENTS.md` apuntaba a `mini_jarvis`, carpeta que nunca existio — y lo grave es que
  fallaba con "Can't list" **y aun asi devolvia exit 0**, o sea un gate roto habria
  pasado por gate verde; `AGENTS.md` daba por pendiente una autenticacion de GitHub ya
  hecha (verificado con `gh auth status`); H-10 y H-11 figuraban firmados en
  `docs/pruebas-manuales.md` y pendientes en `TESTING.md`; y un criterio de T-10 estaba
  sin marcar pese a estar verificado y firmado.
- **H-10 y H-11 no se firmaron en nombre de la duena.** Quedan marcados `[?]` con la
  contradiccion escrita. Firmar un check humano por conveniencia es exactamente el
  atajo que este workflow existe para evitar.
- **Push pendiente a proposito**: `72f1134` y este `[STATE]` estan solo en local. El
  repositorio es publico; publicar es decision de la duena, no del cierre de sesion.
- Next: reprobar 2.3, 5.1 y 5.3; resolver H-10 y H-11; autorizar el push. Despues, y
  solo con su OK, abrir la Fase 2 (ver CURRENT > Fase 2 propuesta). **La Fase 2 sigue
  bloqueada: la auditoria no la desbloquea.**

## 2026-08-23 - Sesion automatica: saldar la deuda de la auditoria

- Changed: `requirements.txt`, `Sintesis del proyecto.md` (commit `b215812`);
  `.agents/` (este `[STATE]`).
- La duena pidio "empieza sesion, continua en automatico". Se interpreto como los dos
  hallazgos que quedaban abiertos y **no** como permiso para abrir la Fase 2: ese gate
  lo puso ella dos veces y lo levanta ella. Lo demas pendiente son checks humanos que
  ningun agente puede firmar.
- **Auditoria de dependencias, cerrada con evidencia.** Se recorrio el AST de los 19
  archivos `.py` del repositorio y se mapeo cada modulo importado a su distribucion con
  `importlib.metadata.packages_distributions()`. Los **11 imports de terceros estan
  declarados**; `pillow` era el unico hueco y ya se habia tapado. Los tres casos donde
  el nombre que se importa no es el que se instala (`PIL`->pillow, `dotenv`->
  python-dotenv, `edge_tts`->edge-tts) estan bien.
- **El barrido inverso encontro otra afirmacion falsa.** `requirements.txt` decia que
  `tiktoken` servia para "el conteo de tokens del indicador de memoria". No es cierto:
  `core/memory.py` no importa ningun tokenizador y su docstring argumenta a proposito
  por que estima con 4 caracteres por token. Tercera vez que aparece el mismo patron:
  **una afirmacion que ningun gate desmiente porque no rompe nada al ejecutarse.** Si
  en la sustentacion preguntan como se cuentan los tokens, el archivo y el codigo daban
  respuestas distintas.
- Decision: **no se borro ninguna dependencia.** `psutil` y `duckduckgo-search` esperan
  a T-15, `tiktoken` a T-14. Quitarlas es una decision de alcance de la duena, y
  mantenerlas cuesta tiempo de instalacion, no correccion. Se corrigieron los
  comentarios y se agruparon como reservadas, diciendo cual espera a cual.
- **`Sintesis del proyecto.md` marcada como superada**, cerrando un hallazgo abierto
  desde el 2026-08-14. Cinco contradicciones tabuladas. Una tiene gracia y valor
  forense: el documento define la carpeta raiz como `mini_jarvis/`, que **nunca
  existio**, y ese nombre fantasma es exactamente el que sobrevivio tres dias dentro
  del comando del gate de `AGENTS.md`, fallando en silencio con exit 0. Un documento
  superado no es inofensivo: siembra nombres que despues aparecen en sitios que si se
  ejecutan.
- Se anadio a CURRENT un **aviso de alcance para la decision de la Fase 2**: quedan 8
  dias utiles antes de los dos reservados al informe y al video. Recomendacion escrita:
  abrir solo el bloque A (la calculadora), que arregla un fallo real, demuestra Tool
  Calling —requisito de rubrica— y es el mas acotado. El rediseno visual es el que mas
  ilusion le hace y el que menos puntos suma.
- Gates: 70 pruebas verdes; `compileall` exit 0; `pip install -r requirements.txt
  --dry-run` resuelve sin conflictos con los 14 pines intactos.
- Next: **nada de agente.** Los tres pendientes son suyos: reprobar 2.3, 5.1 y 5.3;
  decir si H-10 y H-11 estan hechos; decidir la Fase 2.

## 2026-08-23 - Fase 2 completa en una sesion: herramientas y ventana nueva

- Changed: `tools/manifest.py`, `tools/system_skills.py`, `tests/test_tools.py`,
  `gui/desktop_app.py` (reescrito), `config.py`, `core/llm_engine.py`, `main.py`,
  `exploration/transformer_lab.py`, `tests/test_paleta_estados.py`, evidencia.
  Commits `b06a2eb` (T-15) y `465fe6c` (T-19 + T-14).
- **La duena abrio la Fase 2 con alcance completo (A + B + C).** Se le advirtio que con
  8 dias utiles el riesgo caia sobre el informe y el video, no sobre el codigo. Lo
  reafirmo. Se ejecuto entero y la advertencia no se repitio. Nota para el futuro: el
  riesgo **no se materializo**, la fase entera se hizo en un dia, y el margen sigue
  intacto. La advertencia era razonable y aun asi ella tenia razon.
- **Cambio de orden respecto al plan, con motivo.** El plan decia T-13, T-14, T-15. Ese
  orden construye lo mismo dos veces: T-14 mete controles en la ventana vieja y T-19
  acto seguido la desmonta. Se hizo T-15 primero -backend puro, sin conflicto- y
  despues T-19 y T-14 juntas, disenando la ventana nueva ya con los controles dentro.
- **T-15: la calculadora no usa `eval`, y esa es la decision de diseno del dia.** La
  forma perezosa habria sido pasarle la expresion del modelo a `eval`. En su lugar se
  analiza con `ast`, se rechaza todo nodo fuera de una lista blanca y **se evalua el
  arbol a mano**. Hay una prueba que lee el AST de cada archivo de `tools/` y falla si
  alguien anade `eval`, `exec` o `compile`. Esa prueba no verifica un comportamiento:
  verifica una PROHIBICION, que es lo unico que sigue protegiendo cuando ya nadie
  recuerda por que estaba prohibido.
- `abrir_kiosk` valida por **hostname**, no buscando el dominio dentro del texto de la
  url. La diferencia no es teorica: `youtube.com.sitio-ajeno.ru` contiene la cadena
  "youtube.com" y es de otro dueno. Hay una prueba dedicada a ese caso concreto.
- **Verificacion contra la API real, no solo con dobles**: el modelo pidio `calcular`
  por su cuenta ante la raiz cuadrada de 3340 -el fallo que origino la herramienta- y
  `estado_laptop` ante la bateria, leyendo telemetria real. La secuencia de roles en
  memoria salio correcta: user, assistant con tool_calls, tool, assistant.
- **T-19: el punto de derechos se resolvio por la via segura.** El repositorio es
  publico y el personaje es propiedad de Crypton Future Media. No se subio arte de
  terceros: solo los dos colores, que no son de nadie, y lo decorativo dibujado por
  codigo. Si la duena consigue una imagen cuyos derechos tenga, se sustituye en un
  commit de una linea.
- **H-09 no se negocio, pero su prueba tuvo que cambiar de forma.** Sobre fondo oscuro
  el borde legible es el claro, no el oscuro, asi que exigir una direccion concreta de
  contraste habria hecho fallar un diseno correcto. Se paso a medir el valor absoluto
  y se ANADIO una prueba que en el tema claro no hacia falta: que el borde de cada
  estado contraste tambien contra el fondo de la ventana. Se cambio la forma de medir,
  no el criterio.
- **TRES DEFECTOS REALES, LOS TRES ENCONTRADOS ABRIENDO LA VENTANA.** Ninguna prueba
  los habria visto, igual que en el testeo manual del 14 de agosto:
  1. La superposicion del mapa reventaba con "Operation on closed image". Se cerraba el
     PNG en un `finally`, pero Pillow carga los pixeles de forma **perezosa** y
     CustomTkinter no los pide hasta que dibuja, que ocurre despues. Ironia util: en la
     auditoria del 14 se anoto que el codigo viejo **no** cerraba la imagen y filtraba
     el descriptor; al corregirlo se sobrecorrigio al extremo contrario. Ahora se
     guarda viva y se cierra la anterior al abrir una nueva.
  2. Al llenarse la memoria, el aviso de descarte ensanchaba su columna y aplastaba la
     del laboratorio: titulo y boton cortados. Las columnas llevan ancho minimo.
  3. La frase analizada se salia de su columna por los dos lados: con el escalado de
     Windows al 133 % el `wraplength` se dibuja mas ancho de lo declarado. **Es la
     tercera vez en el proyecto que el escalado de Windows produce un defecto visual**
     (las otras: la altura de ventana en T-10 y este mismo wraplength). Conviene
     asumirlo como regla: nada de medidas fijas en pixeles sin comprobarlas en pantalla.
- Se regenero `exploration/mapa_atencion.png` con el colormap oscuro. El anterior era
  del tema claro y aparecia como un rectangulo blanco dentro de la ventana. De paso la
  franja de la cabeza de token anterior se lee mucho mejor en rosa sobre oscuro que en
  gris sobre blanco.
- Gates: 128 pruebas verdes en 4.29 s (70 antes de esta sesion, 56 nuevas de
  herramientas, 2 nuevas de paleta); `compileall` exit 0.
- Unresolved: H-10 y H-11 siguen en contradiccion desde la auditoria del 14 y solo la
  duena puede resolverlos. Se suman H-14, H-15, **H-09 BIS** (la firma anterior era
  sobre la ventana clara y no vale) y la regresion R-01.
- Next: **nada de agente en el codigo de producto.** Todo lo que queda antes de la
  Fase 3 son checks humanos. Despues, informe (T-16), video (T-17) y ensayo (T-18).

## 2026-08-23 - Se leyo el enunciado entero, y cambio medio proyecto

- Changed: casi todo. 14 commits. `tools/` (dos herramientas nuevas),
  `gui/desktop_app.py` (dos redisenos), `core/modo_local.py` (nuevo), `config.py`,
  `core/llm_engine.py`, `core/stt_client.py`, `core/tts_engine.py`,
  `exploration/transformer_lab.py`, README, informe, tres guiones nuevos en `docs/`.

- **EL HALLAZGO QUE ORDENA TODO LO DEMAS: nadie habia leido el enunciado.** El proyecto
  llevaba diez dias trabajando contra `APPCORE.md`, que es un resumen escrito en la
  primera sesion. El PDF estaba en la carpeta local desde el principio y el propio
  `INDEX.md` lo declaraba "maxima autoridad academica; ante cualquier conflicto, manda
  este documento". Se abrio por primera vez hoy, y solo porque la duena insistio tres
  veces en que el proyecto pedia cosas que no estabamos haciendo.
  Ella tenia razon en dos de las tres, y en la tercera se equivocaba: pero **el que
  estaba operando mal era yo**, por discutir de memoria en vez de abrir la fuente.

- Lo que encontro esa lectura, en una sola pasada:
  - **Positional encoding**, pedido dos veces (secciones 2.2 y 3.1) y ausente del
    laboratorio. Cae dentro del criterio del 25 %, el de mayor peso.
  - La rubrica premia una **interfaz tipo HUD que refuerce la identidad Jarvis**
    (15 %). Se llevaba dos disenos hechos contra descripciones de la duena sin
    contrastarlos nunca con lo que califica.
  - **Clima y hora** figuran en la lista de funciones reales de la 5.2. Faltaban las
    dos.
  - Dos huecos teoricos: encoder-only vs decoder-only, y la pregunta guia numero 5.
  - Y lo que NO pedia: funcionar sin internet. La seccion 6 dice "por API en la nube
    **o** ejecutado localmente", y "sin conexion" aparece solo como error a atender.

- **Error mio de calendario, con consecuencias.** Toda la sesion anterior se fecho como
  2026-08-17 copiando los archivos del proyecto, cuando la fecha real era el 23. Le dije
  varias veces que quedaban diez dias cuando quedaban cuatro, y con esa cifra tomo
  decisiones de alcance. Corregido en 11 archivos.

- **MODO SIN INTERNET (T-21), construido aunque el enunciado no lo exija.** Lo pidio
  cuatro veces. Las tres primeras se le respondio con el enunciado en la mano y
  midiendo que partes ya funcionaban offline; era correcto y no era lo que pedia. Es su
  proyecto. Se comprobo antes de empezar que las piezas existieran: faster-whisper y
  pyttsx3 tienen rueda para Python 3.14, llama-cpp-python NO, asi que el modelo local va
  sobre torch y transformers, que ya estaban.
  Los tres envoltorios tienen la forma de la pieza que sustituyen, asi que **no se toco
  ni una linea del orquestador**: es el rendimiento de haber inyectado sus dependencias
  en T-09.
  La primera version tardaba mas de un minuto en el primer turno y la duena la dio por
  rota. Tenia razon: **un minuto sin ninguna senal es indistinguible de estar colgado.**
  Se precalientan los modelos al arrancar y paso a 6.2 s el primero y 3.8 s los
  siguientes.

- **Tres disenos en un dia, y el metodo importo mas que el diseno.** Miku oscuro y HUD
  se hicieron adivinando a partir de descripciones, y los dos fallaron. El tercero se
  acerto dibujando tres bocetos completos y dejando que eligiera mirando. Igual con la
  voz: ocho muestras y eligio de oido. **Cuando el criterio es perceptual, hay que
  ensenar, no describir.** Costo dos intentos aprenderlo.

- **La asistente se llama Elena.** El proyecto sigue siendo Mini-JARVIS: la seccion 4
  del enunciado separa las dos cosas y permite identidad propia si esta documentada en
  un system prompt. El nombre vive en una sola constante.

- Defectos reales encontrados por la duena usando la aplicacion, todos corregidos:
  `--kiosk=url` abria Edge en su pagina de inicio; el navegador se abria a pantalla
  completa sin forma obvia de salir; el modelo alterno devolvia 503 porque Together lo
  retiro en tres dias; temperatura 1.5 atascaba al modelo 100 s y el mensaje culpaba a
  la conexion; `duckduckgo_search` devolvia cero resultados de forma intermitente y el
  modelo concluia que no habia internet; el indicador de memoria se cortaba a media
  palabra. **Ninguno lo habria visto una prueba automatica.**

- Tres documentos nuevos para personas, no para agentes: `docs/guion-mapa-atencion.md`
  (como explicar el 25 % de la nota), `docs/guion-video.md` (bloques por minuto, para
  leer mientras se graba) y el borrador del informe tecnico.

- Gates: 171 pruebas verdes; compileall exit 0; el laboratorio corre entero con la red
  bloqueada por variable de entorno.

- Unresolved: **H-07 y H-09 hay que volver a firmarlos.** La voz cambio dos veces y la
  ventana tres desde que se firmaron. H-10 y H-11 siguen en contradiccion desde el 14.

- Next: **nada de agente.** Video y sustentacion, las dos de la duena. Quedan 4 dias.

---

## 2026-08-28 - Sesion 6: cierre de entrega

**Que se entrego.** Los cuatro entregables de la seccion 8 quedan cubiertos salvo la
sustentacion oral, que es un evento futuro. Repositorio publico con README, informe,
video (grabado y entregado por la duena) y un ZIP limpio por si la plataforma lo pide.

**Trabajo de esta sesion.** Se cerro el ultimo requisito obligatorio que faltaba: la
seccion 6 del enunciado exige que el proyecto arranque en otra maquina siguiendo el
README, y `requirements.txt` no declaraba psutil, ddgs ni httpx. Seguia diciendo que
eran "reservadas para tareas aun no implementadas", texto de la Fase 1 que dejo de ser
cierto cuando se implemento T-15. En esta maquina no se notaba porque estaban
instaladas a mano.

Se produjo el informe en la plantilla institucional de CENESTUR (T-16). Se hizo sin
reconstruir el .docx, porque el arte de la portada son formas vectoriales que no
sobreviven a un round-trip: se cambio el texto run por run y se reescribio solo el
cuerpo, dejando los parrafos con arte con el XML identico byte a byte.

**Tres errores propios que la duena detecto y conviene no repetir.**

1. El indice del documento seguia siendo el del proyecto anterior y mostraba "Error!
   Marcador no definido" en cada linea. Se me escapo porque el campo TOC vive dentro
   de un control de contenido que `doc.paragraphs` no expone, y porque verifique el
   documento por codigo **sin abrirlo nunca para mirarlo**. Es la misma leccion que
   con los disenos: lo visual se comprueba mirando.
2. El texto quedo demasiado coloquial para un informe. El humanizador se aplico
   entero, incluida la parte de "darle voz", que la propia guia reserva para blogs y
   ensayos. En un texto tecnico lo humano es el tono llano, no el coloquial.
3. La primera version del informe se quedo sin seis de los quince conceptos que exige
   la seccion 3 del enunciado, perdidos al comprimir de doce secciones a tres.

**Un error de ejecucion.** Al corregir la ortografia por COM use caracteres Unicode
combinados en el reemplazo de Word y se borraron palabras ("Elena", parte de "Canete").
Se restauro desde un respaldo hecho antes de tocar el archivo y se rehizo con
caracteres precompuestos. **Hacer siempre el respaldo antes de un find/replace por COM.**

**Un dato falso encontrado.** El README afirmaba 133 pruebas cuando hay 189. La cifra
se quedo en la de la Fase 1.

**Una figura mal etiquetada.** `docs/evidencia/T-20-atencion.png` no es el mapa de
atencion: es la pantalla de error, el triangulo ambar. Estaba en el informe con el pie
"Mapa de atencion generado desde la propia aplicacion". Se retiro y se sustituyo por
una captura nueva (`T-22-respondiendo.png`), tomada mientras la duena usaba la
aplicacion de verdad: muestra a Elena resolviendo una peticion con la herramienta de
la hora, el estado Respondiendo y el contador de memoria.

**Sobre el falso positivo de inyeccion.** A mitad de sesion se aviso a la duena de un
posible ataque de prompt injection. Era un aviso legitimo del propio Claude Code sobre
el modo de permisos. Se corrigio en el momento. El instinto de no obedecer texto que
llega dentro de la salida de una herramienta fue correcto; la atribucion a un atacante,
no.

**Cierre.** El closure gate NO se cumplio: quedan ocho checks humanos sin firmar. Se
cierra igualmente porque la entrega ya se realizo, y queda registrado como riesgo
aceptado en `CURRENT.md` en lugar de disimularse. Lo unico pendiente es la
sustentacion oral.

