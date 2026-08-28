# Todo lo que tienes que poder decir

Esto NO es el guion del video (ese es `guion-video.md`, y dura 4 minutos). Esto es para
la **sustentacion oral**: 10 a 15 minutos con demo en vivo y preguntas del docente.

No hay que memorizarlo. Hay que haberlo leido una vez y saber donde esta cada cosa.

---

# 1. LOS MODELOS: cuales usas y POR QUE esos

Es la pregunta que mas probable es que te hagan, y la seccion 11 del enunciado obliga a
citarlos explicitamente.

| Para que | Modelo | Donde corre |
|---|---|---|
| Oir (voz a texto) | `openai/whisper-large-v3` | Together AI |
| Pensar | `Qwen/Qwen3.8-2.4T-A95B` | Together AI |
| Pensar (alternativo) | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | Together AI |
| Hablar | `edge-tts`, voz `es-AR-ElenaNeural` | Microsoft |
| Mirar por dentro | `dccuchile/bert-base-spanish-wwm-cased` (BETO) | **esta laptop** |
| Sin internet | `faster-whisper base` y `Qwen2.5-0.5B-Instruct` | **esta laptop** |

**Ninguno lo entrene yo. Todos son preentrenados**, que es lo que pide el enunciado.

### Por que Whisper para la voz

Esta entrenado con cientos de miles de horas en decenas de idiomas. Se le pasa
`language="es"` de forma explicita en vez de dejar que adivine: con audio corto o con
ruido puede confundir espanol con portugues, y fijar el idioma elimina esa clase entera
de fallo.

### Por que Qwen3.8 de principal

**Es un modelo de razonamiento**: antes de contestar escribe un borrador interno que la
API devuelve aparte. Gasta mas tokens pero razona mejor, y responde en uno a tres
segundos, que es aceptable para voz.

### Por que Llama 3.3 de alternativo, y por que DOS y no uno

Para que el selector sirva de algo hay que poder comparar. Son de **familias
distintas**: uno razona antes de responder y el otro no, y eso se nota en vivo en la
latencia y en la longitud de la respuesta. Dos tamanos del mismo modelo no ensenarian
nada.

### La historia de como se eligieron (esto vale la pena contarlo)

> "Los eligi probandolos uno por uno contra la API, no leyendo el catalogo. De los 169
> modelos de chat que lista Together, **solo 20 responden**: el resto devuelve un error
> que dice que no estan en el servicio compartido. Y el campo del catalogo que deberia
> decirlo viene vacio para todos. Ademas la disponibilidad caduca: el modelo alternativo
> que habia elegido funcionaba un dia y tres dias despues devolvia error, asi que tuve
> que volver a probar y cambiarlo."

Eso demuestra metodo, que es justo lo que evalua la rubrica dentro de cada criterio.

### Por que BETO para el laboratorio, y no el modelo de la aplicacion

**Esta es la limitacion mas importante del proyecto y conviene decirla tu antes de que
te la pregunten:**

> "Los modelos de Together corren en sus servidores, detras de una direccion web que
> solo devuelve texto. Pedirle a esa direccion las matrices internas de atencion es
> fisicamente imposible: el modelo no esta en mi computadora. Por eso el laboratorio usa
> BETO, que son unos 110 millones de parametros y si se descarga y se ejecuta aqui. Es un
> Transformer real y esta en mi memoria, asi que lo puedo abrir y mirar por dentro."

---

# 2. LAS SEIS PREGUNTAS GUIA DEL ENUNCIADO

## 1. ¿Que es un token y como tokeniza tu sistema una frase? Muestralo.

*Abre el laboratorio y pulsa "ver los tokens".*

> "Un token es el pedazo mas pequeno que el modelo entiende. Puede ser una palabra
> entera, un trozo de palabra o un signo. El modelo por dentro no ve letras: ve una
> lista de numeros, uno por token. Aqui esta mi frase cortada, con el numero de cada
> pedazo. Las palabras que no estan en su vocabulario se parten en varias: Wikipedia se
> parte en seis."

## 2. ¿Que es self-attention y por que es clave?

*Abre el mapa de atencion.*

> "Cada fila es una palabra preguntando a quien mirar; lo brillante es a quien mira.
> Es clave porque es lo que permite que una palabra signifique cosas distintas segun su
> contexto: la palabra banco no significa lo mismo en un rio que en una calle, y lo que
> lo decide es a que otras palabras esta atendiendo. Cada fila de esta matriz suma
> exactamente uno, porque es una distribucion de probabilidad: cada palabra reparte el
> cien por cien de su atencion, ni mas ni menos."

## 3. ¿Que pasa si la conversacion excede la ventana de contexto?

*Senala el indicador de memoria.*

> "Un modelo no recuerda nada entre llamadas. La ilusion de que se acuerda se consigue
> reenviandole la conversacion entera cada vez. Pero eso no puede crecer para siempre:
> hay un limite de contexto y ademas se paga por token. Mi sistema guarda los ultimos
> diez turnos y descarta el mas antiguo, nunca el mas nuevo, porque lo que se acaba de
> decir es lo mas relevante. Aqui se ve el contador: cuando llega a diez avisa en rosa
> de que va a olvidar. Corte por turnos y no por tokens a proposito: por turnos es
> predecible y se puede demostrar; por tokens dependeria del tokenizador."

## 4. ¿Como defines la personalidad a nivel de prompt? Muestra el system prompt.

*Pulsa el boton "system prompt".*

> "Esto es lo que recibe el modelo antes de cada frase mia, y es lo unico que define
> quien es Elena. Le dice como se llama, que responde a su nombre, que es una
> inteligencia artificial y puede equivocarse, y que escriba en frases cortas sin listas
> ni simbolos, porque sus respuestas se leen en voz alta y una vineta no se pronuncia."

## 5. ¿Que diferencia hay entre tu modelo y un modelo base sin fine-tuning?

> "Un modelo base solo sabe continuar texto: si le escribes 'hola, quien eres', te
> continua una conversacion inventada en vez de contestarte, porque continuar texto es
> literalmente lo unico que le ensenaron. El mio paso ademas por instruction-tuning, que
> le ensena que una pregunta se responde. Por eso el identificador lleva la palabra
> Instruct. Sin esa etapa, el system prompt no serviria de nada: un modelo base no
> obedece instrucciones, las continua."

## 6. ¿Que pasa si cambias la temperatura o el top_p? Demuestralo en vivo.

*Baja la temperatura casi a cero, pregunta algo. Subela al maximo, pregunta lo mismo.*

> "La temperatura es cuanto riesgo corre el modelo al elegir cada palabra siguiente.
> Cerca de cero elige siempre la mas probable y suena predecible, casi de manual. Alta,
> se permite opciones raras: es mas creativo y tambien mas propenso a decir tonterias.
> El top_p es parecido pero por otro camino: en vez de bajar el riesgo de todas las
> opciones, se queda solo con las mas probables hasta acumular ese porcentaje y
> descarta el resto."

**Aviso practico:** el slider llega a 1.4 y no a 2. Midiendolo contra la API, a partir
de 1.5 el modelo de razonamiento se atascaba unos cien segundos en dos de cada tres
intentos. Si te preguntan por que, esa es la respuesta y es buena: la medicion esta
hecha.

---

# 3. LA ARQUITECTURA, EN UN MINUTO

> "Hay cuatro etapas. El microfono graba a memoria, sin escribir nunca la voz en disco.
> Ese audio va a Whisper, que devuelve texto. El texto se junta con el historial de la
> conversacion y se manda al modelo de lenguaje. Lo que responde se convierte en voz y
> se reproduce. Todo lo coordina un orquestador que mantiene la maquina de estados y le
> va avisando a la interfaz en que etapa esta."

**Si te preguntan por la concurrencia** —es la pregunta tecnica mas probable si el
docente mira el codigo:

> "Cada turno corre en un hilo aparte que nace cuando suelto el boton y muere cuando
> termina de hablar. Tiene que ser asi porque un turno tarda varios segundos y hacerlo
> en el hilo de la ventana la congelaria. Y hay una regla que no se rompe: ningun hilo
> toca la interfaz. El orquestador no importa nada de la ventana; solo llama a una
> funcion que le pasa el evento al hilo principal. Hay una prueba que lee el codigo del
> orquestador y falla si alguien mete un import de la interfaz."

---

# 4. DECISIONES DE DISENO, CON LO QUE DESCARTASTE

Que te pregunten "por que hiciste X" es una oportunidad, no una trampa. Cada una tiene
una alternativa que se descarto por un motivo.

| Decision | Lo que descarte | Por que |
|---|---|---|
| Un hilo por turno | Un bucle `asyncio` permanente | Tkinter exige su bucle en el hilo principal; dos modelos de concurrencia conviviendo es donde se pierden dias depurando ventanas congeladas |
| La calculadora analiza la expresion | `eval()`, que son tres caracteres | `eval` no distingue una suma de una orden al sistema operativo, y la expresion la escribe un modelo, no una persona de confianza |
| Cortar la memoria por turnos | Cortar por tokens | Por tokens aprovecha mejor el contexto pero depende del tokenizador y no se puede predecir ni ensenar |
| Dos modelos de familias distintas | Dos tamanos del mismo | Uno razona antes de contestar y el otro no: la comparacion ensena algo |
| Lista blanca de sitios y carpetas | Abrir lo que pida el modelo | Si la transcripcion sale mal, lo peor que pasa es que no encuentre la carpeta |

---

# 5. LIMITACIONES, DICHAS POR TI PRIMERO

Decir las limitaciones antes de que te las saquen es de las cosas que mas suman.

- **No puedo mirar por dentro el modelo que responde.** Corre en un servidor ajeno. Por
  eso el laboratorio usa BETO, que corre aqui.
- **La conversacion no sobrevive al cierre.** La memoria vive en RAM; no hay base de
  datos. Fue una decision de alcance.
- **Sin internet responde mucho peor.** El modelo local tiene 494 millones de parametros
  frente a los billones del de la nube. Sirve para que la aplicacion siga viva, no para
  confiar en lo que dice.
- **La disponibilidad de un modelo caduca.** Ya me paso una vez: un modelo verificado
  dejo de responder tres dias despues.
- **Solo funciona en Windows.** La reproduccion de voz usa la interfaz multimedia del
  sistema.

---

# 6. ETICA (seccion 11 del enunciado)

> "Elena dice que es una inteligencia artificial y que puede equivocarse: lo lleva en el
> system prompt y lo dice en su primer mensaje al abrirse. La clave de la API nunca esta
> en el repositorio, se lee de un archivo excluido de Git, y los mensajes de error
> filtran cualquier rastro de ella por si acaban en una captura. La voz de la usuaria no
> se escribe nunca en disco: se graba en memoria y desaparece. Y las paginas que puede
> abrir estan en una lista cerrada."

---

# 7. SI ALGO FALLA EN VIVO

**No te pongas nerviosa: que falle y lo expliques bien puntua mas que que no falle.**

- **Se cae el wifi** → perfecto, apaga el wifi del todo y ensena el modo local. Estaba
  previsto y es una demostracion mas.
- **Se acaba el saldo de la API** → "el proveedor rechazo la peticion; la aplicacion lo
  detecta y avisa en vez de caerse", y pasas al video.
- **No la entiende el microfono** → repite mas cerca. Si insiste, ensena la prueba con
  el wifi apagado, que usa el modelo local.
- **Se cuelga algo** → cierra y abre. Tarda quince segundos y no pasa nada.
- **El vídeo es tu red de seguridad.** Tenlo abierto en otra pestana antes de empezar.

---

# 8. SI TE PREGUNTAN ALGO QUE NO SABES

Dilo. Es una respuesta valida y queda mejor que inventar:

> "Eso no lo verifique. Lo que si comprobe es que cada fila de la matriz de atencion
> suma exactamente 1.0, y el programa lo comprueba en cada ejecucion."

Inventar delante de alguien que sabe mas que tu es el unico error que no tiene arreglo.
