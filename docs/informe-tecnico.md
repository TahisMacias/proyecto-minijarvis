# Mini-JARVIS — Informe tecnico

**Asistente conversacional por voz con exploracion de la arquitectura Transformer**

Proyecto integrador · Redes Neuronales · Desarrollo de Software · CENESTUR
Britany Macias · agosto de 2026
Repositorio: https://github.com/TahisMacias/proyecto-minijarvis

---

## 1. Que es Mini-JARVIS

Mini-JARVIS es un asistente de voz en espanol que corre como aplicacion de escritorio en
Windows. Se mantiene presionado un boton, se habla, y el asistente transcribe lo dicho,
piensa una respuesta con un modelo de lenguaje real y la contesta en voz alta,
recordando lo que se hablo en turnos anteriores.

Ademas de conversar, **usa herramientas**: resuelve operaciones matematicas de forma
exacta, consulta el estado real de la computadora, busca en internet y abre paginas web
de una lista autorizada.

Y junto a la conversacion, la misma ventana muestra **que le pasa por dentro a un
Transformer** con la ultima frase dicha: en que pedazos se corta, que numero le
corresponde a cada uno, y a que otras palabras presta atencion cada una.

Ese ultimo punto es el motivo de que el proyecto tenga dos modelos y no uno, y se
explica en la seccion 5.

---

## 2. Arquitectura del sistema

### 2.1 El recorrido de un turno

```
   ┌───────────┐   audio WAV     ┌──────────────────┐
   │ Microfono ├────────────────►│  STT · Whisper   │
   └───────────┘   en memoria    │  (Together AI)   │
                                 └────────┬─────────┘
                                          │ texto
                                          ▼
   ┌────────────────┐   historial   ┌──────────────────┐
   │ Memoria        │◄─────────────►│  LLM             │
   │ ultimos 10     │   completo    │  (Together AI)   │
   │ turnos         │               └────────┬─────────┘
   └────────────────┘                        │
                              ¿pide herramienta?
                                    │              │
                                   si             no
                                    ▼              │
                         ┌────────────────────┐    │
                         │ tools/             │    │
                         │ calcular           │    │
                         │ estado_laptop      │    │
                         │ buscar_web         │    │
                         │ abrir_pagina       │    │
                         └─────────┬──────────┘    │
                                   │ resultado     │
                                   └───────►───────┘
                                          │ texto final
                                          ▼
                                 ┌──────────────────┐
                                 │  TTS · edge-tts  │
                                 └────────┬─────────┘
                                          ▼
                                     Altavoces

   Todo lo coordina core/orchestrator.py, que ademas mantiene la maquina de
   estados y avisa a la interfaz de cada cambio.

   El laboratorio del Transformer corre APARTE, en paralelo, sobre la frase
   transcrita, y no forma parte de este recorrido.
```

### 2.2 Los modulos

| Archivo | Responsabilidad |
|---|---|
| `config.py` | Fuente unica de configuracion: credenciales, paleta, identificadores de modelo, limites. Ningun otro modulo lee variables de entorno. |
| `core/audio_capture.py` | Microfono a WAV en memoria, con push-to-talk |
| `core/stt_client.py` | WAV a texto |
| `core/memory.py` | Historial de la conversacion y su recorte |
| `core/llm_engine.py` | Mensajes a respuesta del modelo. **No ejecuta herramientas** |
| `core/tts_engine.py` | Texto a voz reproducida |
| `core/orchestrator.py` | Maquina de estados y el hilo de cada turno |
| `tools/manifest.py` | Lo que el modelo lee para saber que puede pedir |
| `tools/system_skills.py` | Lo que las herramientas hacen |
| `gui/desktop_app.py` | La ventana |
| `exploration/transformer_lab.py` | El laboratorio, independiente del resto |

---

## 3. Fundamentacion teorica, con la salida real del programa

Todo lo de esta seccion sale de ejecutar `python -m exploration.transformer_lab`. No son
cifras de libro: son las que imprime el proyecto, conservadas en
`docs/evidencia/T-11-salida-transformer_lab.txt`.

### 3.1 Tokenizacion — el modelo no lee palabras

Antes de que un texto entre a la red neuronal, un componente llamado **tokenizador** lo
corta en fragmentos de un vocabulario fijo y traduce cada uno a un numero entero. El
modelo, por dentro, solo ve una lista de numeros.

Con el tokenizador real de Qwen2.5 y una frase propia del proyecto, la salida da
**30 tokens**. Y muestra el fenomeno que interesa: las palabras que no estan en el
vocabulario se reconstruyen pegando varios sub-tokens. `Mini-JARVIS` no existe en los
datos de entrenamiento, asi que se parte; y las palabras acentuadas se parten mas que
las demas.

Ese ultimo detalle tiene una explicacion concreta y vale la pena decirla: el
tokenizador de Qwen es **byte-level BPE**, es decir, no trabaja sobre letras sino sobre
los bytes del texto en UTF-8. Una letra acentuada ocupa dos bytes, asi que aparece
partida y con simbolos de aspecto extrano en pantalla. No es un error de codificacion:
es la representacion interna real del modelo.

### 3.2 Embeddings — el significado como lista de numeros

Un **embedding** es un vector que representa el significado de un token dentro de su
contexto. En BETO cada token se representa con **768 numeros**.

Salida real del programa para una frase de 18 sub-tokens mas las dos marcas `[CLS]` y
`[SEP]`:

```
Forma del tensor: (1, 20, 768)
```

- **1** — una sola frase procesada a la vez
- **20** — los tokens de esa frase, marcas incluidas
- **768** — el tamano del vector de significado de cada token

No hay una etiqueta humana para cada uno de esos 768 numeros. Lo que importa es que
tokens con usos parecidos acaban con vectores parecidos, en un espacio que el modelo
aprendio durante su entrenamiento.

### 3.3 Self-attention — quien mira a quien

Es el mecanismo central del Transformer: cada token mira a todos los demas de la frase
(incluido el mismo) y decide cuanto peso darle a cada uno para construir su propio
significado contextual.

Salida real:

```
Numero de capas de atencion devueltas: 12 (BETO tiene 12 capas Transformer).
Forma de UNA capa de atencion: (1, 12, 20, 20)
Suma de esa fila: 1.000000
```

Las cuatro dimensiones: una frase, **12 cabezas** de atencion, y una matriz de 20 x 20
donde la fila es el token que consulta y la columna el token consultado.

**Que la fila sume exactamente 1.0 no es casualidad ni un ajuste.** Cada fila es el
resultado de una funcion *softmax*, que convierte una lista de puntajes en una
distribucion de probabilidad. Significa que cada token reparte el cien por cien de su
atencion entre los demas: ni mas, ni menos. El programa lo verifica en cada ejecucion y
se detiene con un error si alguna vez dejara de cumplirse.

### 3.4 Capas y cabezas, y el mapa de calor

Un Transformer no procesa la frase de una pasada. La recorre por **capas** —doce en
BETO—, y cada capa entiende un poco mas que la anterior. Dentro de cada capa, doce
**cabezas** miran la frase en paralelo, y cada una puede especializarse en un tipo de
relacion distinto.

Se probaron las **144 combinaciones** de capa por cabeza midiendo cuanta atencion pone
cada una en palabras de contenido en vez de en las marcas `[CLS]` y `[SEP]`. La
**capa 6, cabeza 4** resulto ser una *cabeza de token anterior*: cada token le presta
casi toda su atencion a la palabra que lo precede. En el mapa de calor se ve como una
franja iluminada justo a la izquierda de la diagonal, y es un patron clasico y muy
documentado en modelos tipo BERT.

Imagen: `exploration/mapa_atencion.png`.

---

## 4. Decisiones de diseno, con la alternativa que se descarto

### 4.1 Un hilo efimero por turno, en vez de `asyncio`

**Descartado:** un bucle `asyncio` de larga vida, que era la propuesta inicial del
equipo.

**Motivo:** Tkinter obliga a que su `mainloop` viva en el hilo principal. Sostener en
paralelo un segundo modelo de concurrencia es donde se pierden dias depurando ventanas
congeladas. Se eligio un hilo trabajador que nace cuando se suelta el boton y muere
cuando la respuesta termino de sonar.

**Como se protege:** el orquestador **no importa nada de la interfaz**. Su unica salida
es una funcion `notificar(evento)` que la ventana le entrega, y que se limita a reenviar
el evento con `root.after(0, ...)`, la unica forma segura de cruzar de un hilo cualquiera
al de la interfaz. Una prueba automatica lee el codigo del orquestador y falla si alguna
vez apareciera un import de Tkinter.

### 4.2 La calculadora no usa `eval`

**Descartado:** `eval(expresion)`, que son tres caracteres y funciona.

**Motivo:** `eval` no distingue una suma de una llamada al sistema operativo. La
expresion la escribe un modelo de lenguaje, no una persona de confianza.

**Que se hizo:** la expresion se analiza con el modulo `ast`, se rechaza cualquier
elemento que no este en una lista blanca de operaciones y funciones matematicas, y el
resultado se calcula **recorriendo el arbol a mano**. No hay `eval`, `exec` ni `compile`
en todo `tools/`, y una prueba lee el codigo de cada archivo y falla si alguien los
anade en el futuro.

### 4.3 Truncar la memoria por turnos, no por tokens

**Descartado:** recortar el historial contando tokens, que aprovecha mejor la ventana de
contexto.

**Motivo:** el resultado dependeria del tokenizador y seria dificil de predecir y de
verificar. Truncar por turnos es predecible, se puede ensenar en vivo y se prueba entero
sin llamar a ninguna API.

### 4.4 Dos modelos, no uno

El selector ofrece un modelo de razonamiento grande y uno convencional de otra familia.
No es un adorno: uno escribe un borrador interno antes de contestar y el otro no, y la
diferencia se nota en la latencia y en la longitud de la respuesta.

---

## 5. La limitacion mas importante, dicha de frente

**No es posible inspeccionar la atencion del modelo que responde en la aplicacion.**

Los modelos de Together AI corren en sus servidores, detras de un endpoint HTTP que solo
devuelve texto. Pedirle a ese endpoint sus matrices internas de self-attention es
fisicamente imposible: el modelo no esta en esta computadora.

Por eso el laboratorio usa **BETO** (`dccuchile/bert-base-spanish-wwm-cased`, unos 110
millones de parametros, entrenado en espanol), que si se descarga y se ejecuta entero en
la maquina local. Es un Transformer real, y como esta en nuestra memoria se le puede
abrir y mirar por dentro.

Es una limitacion honesta del enfoque, no un atajo: la alternativa habria sido no poder
demostrar self-attention en absoluto.

### 5.1 Una trampa tecnica que casi cuesta el modulo entero

A partir de `transformers 5.x` el backend de atencion por defecto es SDPA, que **no
materializa las matrices intermedias**. Si se pide `output_attentions=True` con SDPA, el
resultado llega vacio **y no se lanza ninguna excepcion**: el programa "corre bien" y no
cumple su objetivo.

La correccion obligatoria es cargar el modelo con `attn_implementation="eager"`. El
laboratorio ademas lo comprueba en tiempo de ejecucion y se detiene con un mensaje
explicito si alguna vez volviera a ocurrir.

---

## 6. Otras limitaciones conocidas

- **La conversacion no sobrevive al cierre.** La memoria vive en RAM. Al cerrar la
  aplicacion se pierde. Fue una decision de alcance: no hay base de datos.
- **La disponibilidad de un modelo caduca.** De los 169 modelos de chat que lista
  Together, solo 20 responden; el resto devuelve `HTTP 400 non-serverless`. Y el campo
  `running` del catalogo no sirve para saberlo: viene en `false` para todos. Peor aun:
  el modelo alterno elegido el 14 de agosto, verificado entonces contra la API, devolvia
  `HTTP 503` tres dias despues. **Haber probado un modelo no lo garantiza para siempre.**
- **La temperatura tiene un tope de 1.4.** Midiendo contra la API, a partir de 1.5 el
  modelo de razonamiento se atasca unos 100 segundos en dos de cada tres intentos.
- **Un microfono que capta solo ruido no es un fallo detectable**: produce una
  transcripcion equivocada, no vacia, y se atiende como conversacion normal.
- **Solo Windows.** La reproduccion de voz usa la interfaz multimedia del sistema.

---

## 7. Manejo de errores

El diseno preveia siete fallos. Los siete estan cubiertos con un mensaje propio,
redactado para una persona, sin trazas tecnicas: microfono no disponible, sin conexion,
credenciales invalidas, transcripcion vacia, respuesta vacia del modelo (con un
reintento unico), JSON de herramienta malformado, y fallo de la sintesis de voz.

La regla que los une: **cualquier excepcion que no venga de un modulo del proyecto se
reemplaza por un mensaje generico**, para que una traza tecnica no llegue nunca a la
pantalla. Y todo camino de fallo termina igual:

```
... -> ATENCION -> REPOSO
```

Nunca se queda en ATENCION ni en PENSANDO. Esa invariante impide el sintoma mas dificil
de diagnosticar en vivo: una aplicacion que no se cerro pero se quedo muda para siempre.

Detalle completo en `docs/evidencia/T-12-cobertura-de-errores.md`, que incluye tambien
lo que **no** se cubre.

---

## 8. Accesibilidad de la interfaz

Los cuatro estados de actividad se distinguen **por color y por forma**, no solo por
color: circulo que late, tres puntos, onda y triangulo. Una persona con daltonismo debe
poder operar la aplicacion; si la unica pista fuera el color, para ella la interfaz no
comunicaria nada.

Que dos estados compartieran color es un fallo automatico del proyecto, y hay pruebas
que lo impiden: verifican que los cuatro tengan color propio, forma propia, y contraste
suficiente contra su relleno y contra el fondo de la ventana.

---

## 9. Verificacion

- **133 pruebas automaticas**, en unos 4 segundos, sin red, sin microfono y sin gastar
  saldo de API.
- **50 commits** con historial progresivo, uno por tarea.
- Las pruebas mas utiles del proyecto no comprueban comportamientos sino
  **prohibiciones**: que el orquestador no importe la interfaz, que `tools/` no contenga
  `eval`, que dos estados no compartan color. Un comportamiento correcto puede volver a
  romperse; una prohibicion verificada no.

### 9.1 Lo que las pruebas no vieron

Conviene decirlo porque es el hallazgo mas util del proyecto. Varios defectos reales no
los encontro ninguna prueba automatica, sino usar la aplicacion:

- Whisper respondia "gracias" ante el silencio, porque alucina con audio vacio.
- El verde menta se veia azul en pantalla: como decoracion los pasteles funcionan, como
  senal no.
- El estado de aviso se emitia correctamente y aun asi nadie lo veia, primero porque
  duraba microsegundos y despues porque ocurria en una columna distinta de donde estaba
  mirando la usuaria.
- El README declaraba un modelo que la aplicacion ya no usaba.
- `--kiosk=direccion` abria el navegador en su pagina de inicio: el comando estaba bien
  formado y significaba otra cosa para el programa que lo recibia.

**Todos viven en la frontera entre el codigo y la percepcion de una persona.** Ninguna
prueba automatica los habria detectado, porque en todos los casos el programa hacia
exactamente lo que decia hacer.

---

## 10. Modelos y proveedores utilizados

| Etapa | Proveedor | Modelo | Costo |
|---|---|---|---|
| Transcripcion | Together AI | `openai/whisper-large-v3` | $0.0015 / min de audio |
| LLM predeterminado | Together AI | `Qwen/Qwen3.8-2.4T-A95B` | $2.50 / $6.25 por millon |
| LLM alterno | Together AI | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | $1.04 / $1.04 por millon |
| Sintesis de voz | Microsoft | `edge-tts`, voz `es-MX-DaliaNeural` | sin costo |
| Tokenizacion (laboratorio) | Hugging Face | tokenizador de `Qwen/Qwen2.5-7B-Instruct` | sin costo |
| Embeddings y atencion | Hugging Face | `dccuchile/bert-base-spanish-wwm-cased` | sin costo |

Ningun modelo fue entrenado por el equipo. Todos son preentrenados, como exige el
enunciado.

---

## 11. Consideraciones eticas

El system prompt declara explicitamente que Mini-JARVIS **es una inteligencia artificial
y que sus respuestas pueden contener errores**, y la aplicacion lo dice tambien en su
primer mensaje al abrirse. No se presenta como una persona.

Ninguna credencial vive en el repositorio: la clave de API se lee de un archivo `.env`
excluido de Git, y los mensajes de error filtran cualquier rastro de ella antes de
mostrarse, porque el repositorio es publico y una captura de pantalla podria acabar en
el informe o en el video.

La voz de la usuaria **nunca se escribe en disco**: se graba en memoria y desaparece
cuando nadie la referencia. Es un dato personal y no se conserva.

`abrir_pagina` solo abre paginas de una lista blanca cerrada, validando el dominio real
de la direccion antes de construir el comando.
