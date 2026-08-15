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
- [X: no es verde es azul] **2.3** Mientras hablas, el circulo esta **verde y latiendo**. Es la senal de
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

- [FALLO: por defecto ubica el texto "gracias"] **5.1** Presiona y **suelta de inmediato**, sin decir nada -> debe aparecer un
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
