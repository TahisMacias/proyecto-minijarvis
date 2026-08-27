# Guion del video demostrativo

Duracion objetivo: **3 minutos y medio**. El enunciado pide entre 2 y 4 (seccion 8).

El video tiene DOS trabajos, y el segundo es el que la gente olvida:

1. Ensenar el asistente funcionando en un caso de uso real.
2. **Servir de respaldo si la demo en vivo falla.** Si el dia de la sustentacion se cae
   el wifi de la sala o Together AI tiene un mal momento, este video es lo que salva la
   nota. Por eso hay que grabarlo con todo funcionando y sin prisa.

---

# QUE CUBRE ESTE VIDEO, Y QUE NO

La rubrica reparte 100 puntos en seis criterios. **El video llega directamente al 65 %**;
el resto se juzga mirando el repositorio, leyendo el informe y hablando contigo.

| Criterio | Peso | ¿Se ve en el video? |
|---|---|---|
| Comprension del Transformer y del LLM | **25 %** | **SI** — bloque del laboratorio (1:50) |
| Funcionalidad del asistente de voz | **25 %** | **SI** — el turno completo (0:20) |
| Interfaz y experiencia de usuario | 15 % | **SI** — se ve sola, y se narran los estados |
| Calidad del codigo | 15 % | no: se juzga del repositorio |
| Informe tecnico | 10 % | no: es el documento |
| Sustentacion y demo en vivo | 10 % | **el video ES el respaldo** si la demo falla |

Por eso el bloque del laboratorio no se recorta nunca: es el unico sitio del video
donde se demuestra el criterio de mas peso.

Y por eso conviene narrar lo que se ve en pantalla en vez de callarse: la rubrica dice
que dentro de cada criterio se evalua **"la claridad con la que el equipo puede explicar
sus decisiones"**. Ensenar sin explicar deja la mitad de los puntos sobre la mesa.

---

## ANTES DE GRABAR — seis comprobaciones de dos minutos

- [ ] **Wifi encendido** y funcionando.
- [ ] **Saldo en Together AI.** Entra a la web y miralo. Si se acaba a mitad de la
      grabacion, se pierde la toma entera.
- [ ] **Abre la aplicacion y espera medio minuto** antes de empezar. Los modelos del
      modo sin internet se cargan en segundo plano y conviene que esten listos.
- [ ] **Habla una vez de prueba**, fuera de la grabacion, para comprobar el microfono y
      el volumen. Que se te oiga a ti y que se oiga a Elena.
- [ ] **Cierra todo lo demas**: navegador, chats, notificaciones. Que no salte un aviso
      de WhatsApp en mitad del video.
- [ ] **Silencia el telefono.**

Para grabar: `Win + G` abre la barra de juego de Windows y graba la pantalla con audio.
No hace falta instalar nada.

**Si algo sale mal a mitad, para y vuelve a empezar.** Es mejor grabar cuatro veces que
entregar una toma con un fallo. Nadie ve los descartes.

---

# EL GUION

Lo que va **entre comillas** es lo que dices tu. Lo que va en *cursiva* es lo que haces.

---

## 0:00 – 0:20 · Quien eres y que es esto

> "Hola, soy Britany Macias, de Desarrollo de Software en CENESTUR. Este es
> Mini-JARVIS, mi proyecto integrador de Redes Neuronales. La asistente se llama Elena
> y funciona por voz: se mantiene presionado un boton, se le habla, y ella transcribe,
> piensa y responde en voz alta."

*Ten la ventana abierta y quieta. Que se vea entera.*

---

## 0:20 – 1:10 · El pipeline completo, con los estados

> "Voy a hablarle. Fijense en la figura de la izquierda, que va cambiando de forma y de
> color segun lo que este haciendo."

*Manten la barra espaciadora y di:*

> **"Hola Elena, ¿quien eres?"**

*Suelta. Mientras responde, ve narrando lo que se ve:*

> "Circulo turquesa latiendo: esta escuchando. Tres puntos azules: esta pensando,
> consultando al modelo. Barras rosas: esta hablando. Los cuatro estados se distinguen
> por color **y por forma**, para que la aplicacion sirva tambien a una persona con
> daltonismo."

*Deja que termine de hablar antes de seguir. No la interrumpas.*

---

## 1:10 – 1:50 · Las herramientas: lo que un modelo NO puede hacer solo

> "Un modelo de lenguaje predice texto, no calcula ni consulta datos. Por eso Elena
> tiene herramientas."

*Manten la barra y di:*

> **"Elena, ¿cual es la raiz cuadrada de 3340?"**

*Cuando responda, senala la linea que dice "usando la herramienta calcular":*

> "Ahi se ve: el modelo no lo calculo de cabeza, pidio la herramienta. Python hizo la
> cuenta y le devolvio el resultado exacto."

*Y una segunda, que ensena que tambien controla la computadora:*

> **"Elena, pon musica de Bad Bunny en YouTube"**

*Cuando se abra el navegador, vuelve a la ventana y remata:*

> "Tiene diez herramientas: calcular, la hora, el clima, el estado de la laptop,
> busqueda web, abrir paginas de una lista autorizada, subir y bajar el volumen y el
> brillo, abrir carpetas y poner musica. Ninguna la ejecuta el modelo: el modelo solo
> PIDE, y mi codigo decide si se hace."

**Esa ultima frase vale mucho** y cuesta cinco segundos: demuestra que entiendes como
funciona el tool calling por dentro, no solo que lo tienes.

---

## 1:50 – 2:40 · El laboratorio del Transformer

**Esta es la parte que mas vale de todo el video.** Es el 25 % de la rubrica.

> "Abajo a la derecha esta el laboratorio. Analiza la ultima frase que dije, con un
> Transformer real corriendo en esta misma computadora."

*Senala la linea del resumen (tokens, la forma, capas x cabezas).*

> "Mi frase se corto en tantos tokens. El modelo no lee palabras: lee pedazos con un
> numero cada uno."

*Pulsa **ver los tokens**. Deja la tabla en pantalla dos segundos.*

> "Aqui se ve cada pedazo con su numero. Las palabras que no estan en el vocabulario se
> parten en varios."

*Cierra y pulsa **mapa de atencion**.*

> "Y esto es self-attention. Cada fila es una palabra preguntando a quien mirar; lo
> rosa es a quien mira. Se ve una diagonal brillante: cada palabra le presta casi toda
> su atencion a la que tiene justo delante. Cada fila de esta matriz suma exactamente
> uno, porque la atencion es una distribucion de probabilidad."

*Cierra la superposicion con el boton rosa.*

---

## 2:40 – 3:10 · Los controles de sustentacion

> "Abajo estan los controles. La temperatura cambia cuanto riesgo corre el modelo al
> elegir cada palabra. El indicador de memoria muestra cuantos turnos recuerda: cuando
> llega a diez, avisa de que va a olvidar el mas antiguo, que es la ventana de contexto
> llenandose. Y se puede cambiar de modelo sin reiniciar, conservando la conversacion."

*Mueve el slider de temperatura de un lado a otro mientras hablas. No hace falta que
generes otra respuesta: se entiende con el gesto.*

---

## 3:10 – 3:30 · Sin internet

> "Y si se cae la conexion, Elena sigue funcionando con modelos que viven en esta
> computadora."

*Apaga el wifi. Manten la barra y di:*

> **"Hola Elena, ¿quien eres?"**

*Senala el aviso ambar de arriba a la derecha:*

> "Ahi avisa: sin internet, modelo local. Responde peor y con otra voz, porque el
> modelo local es muchisimo mas pequeno, pero la aplicacion no se cae ni se queda
> muda."

**NO le preguntes datos aqui.** El modelo local se equivoca: preguntandole dos veces la
capital de Ecuador contesto "Quito" una vez y "Santo Domingo" la otra. Con "quien eres"
responde bien y demuestra exactamente lo mismo.

*Vuelve a encender el wifi.*

---

## 3:30 – 3:45 · Cierre

> "El codigo esta en un repositorio publico, con el informe tecnico y el modulo de
> exploracion, que tambien se puede ejecutar por separado desde la consola. Gracias."

---

# SI SE TE VA DE TIEMPO

Recorta en este orden. Lo de arriba se va primero:

1. La segunda herramienta (YouTube).
2. Los controles de sustentacion enteros (2:40 – 3:10).
3. El modo sin internet.

**No recortes nunca el laboratorio del Transformer.** Vale el 25 % de la nota y es lo
unico que no se puede contar sin ensenarlo.

---

# LAS TRES FRASES QUE SI O SI TIENEN QUE ESTAR

Si acabas grabando a las prisas y solo te da tiempo a tres cosas:

1. **"Hola Elena, ¿quien eres?"** — el pipeline completo con los cuatro estados.
2. **"¿Cual es la raiz cuadrada de 3340?"** — tool calling, y se ve en pantalla.
3. **El mapa de atencion abierto**, explicando la diagonal.

Con esas tres el video cumple lo que pide el enunciado.
