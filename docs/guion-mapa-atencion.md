# Como explicar el mapa de atencion

> **Este documento explica SOLO el mapa.** Todo lo demas que te pueden preguntar en
> la sustentacion -que modelos usas y por que, la arquitectura, las decisiones de
> diseno, las limitaciones y que hacer si algo falla en vivo- esta en
> `guion-sustentacion.md`.

Esto es para la sustentacion oral y para el informe. Es el criterio de mayor peso de la
rubrica: 25 %.

No hace falta saber programar para explicarlo. Hace falta entender tres ideas y poder
senalarlas en la imagen.

---

## Antes de nada: para que sirve el mapa

Los modelos grandes que usa la aplicacion (Qwen) corren en los servidores de Together
AI. Solo devuelven texto. **Es fisicamente imposible pedirles sus tripas**: no estan en
esta computadora.

Por eso el laboratorio usa un modelo pequeno, **BETO**, que si corre entero aqui. Es un
Transformer de verdad, entrenado en espanol, y como esta en nuestra memoria podemos
abrirlo y mirar por dentro.

**Si te preguntan por que no analizas el modelo de la aplicacion, esa es la respuesta**,
y es una limitacion honesta que conviene decir antes de que te la pregunten.

---

## Idea 1 — El modelo no lee palabras, lee pedazos

Prueba a decirle **"Abre Wikipedia"** y mira las etiquetas del mapa:

```
[CLS]   Abre   W   ##i   ##k   ##ip   ##edi   ##a   .   [SEP]
```

*Wikipedia* no existe en el vocabulario de BETO, asi que la parte en seis pedazos. Las
almohadillas `##` significan "esto va pegado a lo anterior, no lleva espacio".

`[CLS]` y `[SEP]` no son palabras: son dos marcas que el modelo pone al principio y al
final para saber donde empieza y acaba la frase.

**Frase para decir en voz alta:**

> "El modelo no ve palabras, ve numeros. Antes de entrar a la red, el tokenizador corta
> el texto en pedazos de su vocabulario. Como Wikipedia no esta en el vocabulario, la
> reconstruye pegando seis pedazos mas pequenos."

---

## Idea 2 — La cuadricula: quien mira a quien

- Cada **fila** es un pedazo preguntando: *¿a quien miro yo?*
- Cada **columna** es el pedazo al que mira.
- **Rosa** = mucha atencion. **Oscuro** = ninguna.

En el ejemplo de arriba se ve una diagonal rosa **corrida un paso a la izquierda**: la
fila `W` se ilumina en la columna `Abre`, la fila `##i` se ilumina en `W`, y asi.

**Cada pedazo esta mirando justo al pedazo anterior.** Van encadenados.

Tiene sentido: como *Wikipedia* esta partida, cada trozo necesita al de antes para
saber que palabra estan formando entre todos.

**Frase para decir en voz alta:**

> "Esto es self-attention. Cada pedazo de la frase decide a cuales de los demas hacerle
> caso para entenderse a si mismo. En esta cabeza concreta, cada uno le presta casi toda
> su atencion al que tiene justo delante."

---

## Idea 3 — Capas y cabezas

Las dos palabras del titulo del grafico.

### Capa 6 de 12

**BETO lee la frase doce veces seguidas.** Cada lectura entiende un poco mas que la
anterior: las primeras casi solo ven letras y trozos, las ultimas ya entienden la frase
completa. Cada lectura es una **capa**.

El mapa muestra la numero 6: la de en medio.

### Cabeza 4 de 12

**En cada lectura hay doce lectores mirando a la vez**, y cada uno busca una cosa
distinta. Uno se fija en quien hace la accion, otro en la puntuacion, otro en la palabra
anterior. Cada lector es una **cabeza de atencion**.

El mapa muestra el numero 4.

### Por que precisamente esa

Hay **144 combinaciones** posibles (12 capas x 12 cabezas). Se probaron todas y se
eligio esta porque es **la mas facil de ver**: la cabeza 4 de la capa 6 resulto ser una
"cabeza de token anterior", y ese patron se reconoce de un vistazo incluso proyectado.

**Frase para decir en voz alta:**

> "Un Transformer no procesa la frase de una pasada. La recorre por capas, y dentro de
> cada capa varias cabezas la miran en paralelo buscando relaciones distintas. Aqui
> estamos viendo una de las 144 combinaciones, elegida porque su patron es el mas
> reconocible."

---

## Dos preguntas mas del enunciado, con su respuesta corta

**"¿Por que los LLM usan arquitectura decoder-only?"**

> "Porque conversar es generar texto. Un encoder como BETO lee la frase entera y la
> entiende muy bien, pero no produce nada nuevo. Un decoder genera palabra por palabra,
> mirando solo hacia atras, que es justo lo que hace falta para responder. En este
> proyecto estan los dos: BETO encoder para mirar por dentro, Qwen decoder para
> conversar."

**"¿Que diferencia hay entre tu modelo y un modelo base sin fine-tuning?"**

> "Un modelo base solo sabe continuar texto: si le escribes 'hola, quien eres', te
> continua la conversacion inventada en vez de contestarte. El nuestro paso ademas por
> instruction-tuning, que le ensena que una pregunta se responde. Por eso el
> identificador lleva la palabra Instruct. Sin esa etapa, el system prompt que define
> la personalidad de Elena no serviria de nada."

## Si te preguntan algo que no sabes

Dilo. Es una respuesta valida y queda mejor que inventar:

> "Eso no lo verifique. Lo que si comprobe es que cada fila de la matriz suma
> exactamente 1.0, porque la atencion es una distribucion de probabilidad: cada pedazo
> reparte el cien por cien de su atencion entre los demas, ni mas ni menos."

Ese dato **esta comprobado de verdad** por el programa cada vez que se ejecuta. Sale
impreso en la consola al correr:

```
python -m exploration.transformer_lab
```

---

## Resumen de una frase, por si te quedas en blanco

> "Cada fila es una palabra preguntando a quien mirar; lo rosa es a quien mira. Aqui
> cada pedazo mira al anterior porque la palabra Wikipedia esta partida en trozos y
> necesitan encadenarse para significar algo."
