# Pruebas manuales — Fase 1 (lado tecnico)

Lo que se prueba aqui es que **el sistema aguante**, no que el modelo sea listo. La
calidad de las respuestas (matematicas, conocimiento, comparacion entre modelos) se
mide aparte y mas adelante.

Regla para todas: **la aplicacion nunca debe quedarse congelada, muda ni cerrarse
sola.** Si algo sale mal, tiene que decirlo con palabras y volver a quedar lista para
otro intento. Ese es el criterio.

Marca con `[x]` lo que pase y anota al lado lo que no.

---

## 1. Arranque

- [X] **1.1** Doble clic en `Iniciar Mini-JARVIS.bat` -> abre la ventana.
- [X] **1.2** El circulo de arriba esta **punteado y quieto** (reposo), y abajo dice
      "Listo. Manten presionado el boton para hablar".
- [X] **1.3** Cierra la ventana con la X -> se cierra entera, sin dejar nada colgado.

## 2. Hablar (las dos formas)

- [X] **2.1** Manten el **boton** con el raton, habla, suelta -> responde.
- [X] **2.2** Manten la **barra espaciadora**, habla, suelta -> responde igual.
- [X] **2.3** Mientras hablas, el circulo esta **verde y latiendo**. Es la senal de
      que si esta grabando.
- [X] **2.4** Al soltar, pasa a **azul con tres puntos** (pensando) y luego a **rosa
      con ondas** (respondiendo).

## 3. Memoria de la conversacion

- [X] **3.1** Pregunta algo. Ejemplo: *"Mi color favorito es el verde"*.
- [X] **3.2** En el turno siguiente pregunta: *"¿Cual dije que era mi color favorito?"*
      -> debe acordarse. Eso prueba que el historial se envia completo.
- [X] **3.3** Encadena un tercer turno con otra referencia al anterior -> sigue el hilo.

## 4. Que no se congele

- [X] **4.1** Mientras esta **pensando o respondiendo**, mueve la ventana arrastrandola.
      Debe moverse con normalidad; nunca debe salir "(no responde)".
- [X] **4.2** Mientras responde, cambia de pestana a **Laboratorio** y vuelve. Responde
      sin trabarse.
- [X] **4.3** Redimensiona la ventana durante un turno -> se acomoda sin romperse.

## 5. Los errores, que es lo que mas importa

- [x] **5.1** Presiona y **suelta de inmediato**, sin decir nada -> debe aparecer un
      aviso amable tipo "No te escuche bien" y volver a reposo. **No** debe quedarse
      pensando para siempre.
- [X] **5.2** Mientras esta respondiendo, presiona la barra otra vez -> te avisa que
      esperes; no abre el microfono encima del turno en curso.
- [FALLO: Se queda en reposo, no muestra error ni durazno con triangulo, solo un aviso en chat que "no se pudo enviar el audio..."] **5.3** **Apaga el wifi** y habla -> mensaje pidiendo revisar la conexion, el
      circulo pasa a **durazno con triangulo** y despues vuelve a reposo.
- [X] **5.4** Vuelve a **encender el wifi** y habla otra vez -> funciona sin reiniciar
      la aplicacion.
- [X] **5.5** En ningun caso aparece texto tecnico raro (`Traceback`, `Error 500`,
      nombres de archivos `.py`). Si aparece, copialo tal cual.

## 6. Los estados sin leer

- [X] **6.1** Mira la ventana **de lejos, sin leer el texto**: ¿sabes en cual de los
      cuatro estados esta, solo por el color y la figura?
- [X] **6.2** Lo mismo entrecerrando los ojos hasta que el color casi no se distinga:
      la **forma** sola deberia bastar. Esto es lo que se le pide a la interfaz para
      que sirva a una persona con daltonismo.

## 7. La pestana Laboratorio

- [X] **7.1** Habla una frase y abre la pestana **Laboratorio**. La primera vez tarda
      unos 20 segundos (esta cargando el modelo); despues es inmediato.
- [X] **7.2** Muestra **tu frase** cortada en tokens con su numero, y el mapa de calor
      de esa misma frase. No una frase de ejemplo: la tuya.
- [X] **7.3** Mientras calcula, la conversacion sigue funcionando.

## 8. El laboratorio por consola

- [X] **8.1** Con el entorno activado: `python -m exploration.transformer_lab`.
      Termina sin errores e imprime tokens, IDs y las formas de los tensores.
- [X] **8.2** Abre `exploration/mapa_atencion.png` -> se ven los tokens etiquetados en
      los dos ejes y una franja clara pegada a la diagonal.
- [X] **8.3** ¿Podrias explicar esa imagen en voz alta a alguien? Si no, dime que
      parte no se entiende: es material de sustentacion.

## 9. Alguien mas

- [X] **9.1** Pidele a otra persona que use la aplicacion **sin explicarle nada** y
      mira donde duda. Lo que a esa persona no le resulte obvio es un defecto de la
      interfaz, no de la persona.

---

## Como reportar lo que falle

Con estas tres cosas basta:

1. Que numero de la lista es.
2. Que hiciste exactamente (que dijiste, que tecla, en que momento).
3. Que aparecio en pantalla, copiado tal cual.


---

# Recorrido de la Fase 2 (17 de agosto)

La ventana cambio entera y hay herramientas nuevas. Esto es lo unico que falta por
probar antes de ponerse con el informe y el video.

**Abre la aplicacion y ve bajando por la lista.** Marca `[X]` lo que salga bien y
escribe al lado lo que no. Tarda unos quince minutos.

## A. Lo primero, antes de hablar: mira la ventana

- [X] **A.1** Abre con doble clic en `Iniciar Mini-JARVIS.bat`. Se abre una ventana
      oscura, ancha, con tres columnas.
- [ ] **A.2** ¿Te gusta? Es tu tematica. Si algo te chirria (un color, un tamano, una
      palabra), anotalo aqui aunque sea una tonteria: es tu proyecto y se cambia.
- [ ] **A.3** A la derecha del todo pone "LABORATORIO DEL TRANSFORMER" y esta vacio.
      Es normal: se llena cuando hables.

## B. Habla. Di estas frases, una por una

Manten presionado el boton (o la barra espaciadora), habla, suelta.

- [X: dio 57.79] **B.1** *"Cual es la raiz cuadrada de 3340"*
      **Esta es la importante.** Es la pregunta que antes no sabia contestar. Ahora
      debe decir un numero: 57.79 y pico. Si dice "aproximadamente" o "no tengo
      calculadora", algo va mal y hay que anotarlo.
- [X] **B.2** *"Como esta la bateria de la laptop"*
      Debe decirte el porcentaje REAL de tu bateria. Compruebalo mirando el icono de
      Windows abajo a la derecha: tienen que coincidir.
- [X] **B.3** *"Busca en internet que es un transformer"*
      Debe darte resultados de verdad, no lo que se sepa de memoria.
- [X: arreglado el 17 ago, commit d2b212a] **B.4** *"Abre Wikipedia"*
      Debe abrirse el navegador a pantalla completa. Cierralo con Alt+F4.
- [X: se nego, correcto] **B.5** *"Abre Facebook"*
      **Debe NEGARSE.** Tiene que decirte con buenas palabras que solo puede abrir
      YouTube, Wikipedia, Google y GitHub. Si abre Facebook, eso es un fallo grave:
      anotalo en mayusculas.

## C. Los estados, otra vez (la firma anterior ya no vale)

El tema cambio de claro a oscuro, asi que lo que firmaste el 14 de agosto era sobre
otra ventana. Hay que volver a mirarlo.

- [ ] **C.1** Habla y **mira la figura grande de la izquierda**, sin leer el texto.
      Mientras hablas: circulo turquesa que late. Al soltar: tres puntos azules.
      Cuando responde: barras rosas. ¿Se distinguen?
- [ ] **C.2** Ahora **entrecierra los ojos** hasta que casi no distingas el color.
      ¿Sigues sabiendo en cual esta, solo por la forma? Esto es lo que hace que la
      aplicacion le sirva a una persona daltonica.
- [ ] **C.3** Alejate un metro de la pantalla. ¿Se sigue entendiendo?

## D. El mapa de atencion

- [ ] **D.1** Despues de hablar, pulsa **"Ver el mapa de atencion"** abajo a la
      derecha. Se abre grande encima de la ventana.
- [ ] **D.2** Se ve una linea de cuadros rosas en diagonal. Eso significa que cada
      palabra esta mirando sobre todo a la palabra anterior. **Es lo que vas a
      explicar en la sustentacion.** ¿Lo entiendes mirandolo? Si no, dime que parte.
- [ ] **D.3** Cierrala con el boton rosa "Cerrar". Prueba tambien la tecla Escape.

## E. Los controles de abajo (para la sustentacion)

- [ ] **E.1** Baja **Temperatura** casi a cero. Di *"cuentame algo sobre la musica"*.
      Fijate en la respuesta.
- [ ] **E.2** Sube **Temperatura** al maximo. Di **la misma frase**. La respuesta debe
      ser mas rara o mas creativa. ¿Notas la diferencia? Es lo que te van a preguntar.
- [ ] **E.3** Cambia el **Modelo** al segundo de la lista y sigue hablando sin cerrar
      nada. Debe seguir acordandose de lo anterior.
- [ ] **E.4** Pulsa **"Ver system prompt"**. Es el texto que se le manda al modelo
      antes de cada frase. Leelo: te lo pueden preguntar.
- [ ] **E.5** Habla diez veces seguidas y mira el renglon de **Memoria**. Cuando
      llegue a 10/10 se pone rosa y avisa de que va a olvidar lo mas viejo.
      **Ese momento es oro para la sustentacion**: es la ventana de contexto
      llenandose delante del tribunal.

## F. Lo que quedo pendiente de la Fase 1

- [ ] **F.1** Presiona y suelta **sin decir nada**. Antes contestaba a "gracias".
      Ahora debe avisarte de que no escucho nada.
- [ ] **F.2** **Apaga el wifi** y habla. Debe avisarte con buenas palabras Y la figura
      debe ponerse en **triangulo ambar** un par de segundos. Antes no se veia.
- [ ] **F.3** Enciende el wifi y habla otra vez. Debe funcionar sin reiniciar.
- [ ] **F.4** En ningun momento debe aparecer texto tecnico raro (`Traceback`, nombres
      de archivos `.py`). Si aparece, copialo tal cual.

## G. Dos preguntas que solo puedes contestar tu

- [ ] **G.1** ¿Alguien ajeno al proyecto llego a usar la aplicacion sin que le
      explicaras nada? (Esto es H-10, y esta apuntado como dudoso.)
- [ ] **G.2** ¿Podrias explicar el mapa de atencion en voz alta a alguien que no ha
      visto el codigo? (Esto es H-11.)
