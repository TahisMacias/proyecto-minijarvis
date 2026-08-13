# Mini-JARVIS — Documento de diseno

Fecha: 2026-08-13
Entrega: 2026-08-27 (14 dias calendario)
Asignatura: Redes Neuronales — Desarrollo de Software, CENESTUR
Estado: aprobado por la duena del proyecto el 2026-08-13

Este documento fija las decisiones de diseno y su justificacion. Esta escrito para
servir tambien como material base del informe tecnico exigido por el enunciado.

---

## 1. Contexto y restricciones

Mini-JARVIS es un asistente conversacional por voz que demuestra de forma aplicada la
arquitectura Transformer. No es software de produccion: su proposito es evidenciar
comprension tecnica ante una rubrica.

Restricciones que no se negocian:

- El LLM debe ser un modelo preentrenado real. Prohibido simular con `if/else`.
- Ninguna credencial en el repositorio.
- El proyecto debe correr en otra maquina siguiendo solo el README.
- Historial de commits progresivo, no un unico commit final.
- Debe existir un modulo que evidencie tokenizacion, embeddings y self-attention.

Restriccion de tiempo: 14 dias calendario. La estimacion de construccion es de 9.75
dias y el cierre documental consume 2.5 mas, dejando menos de dos dias de holgura.
Esa escasez es la que gobierna las decisiones de alcance de la seccion 3.

## 2. Peso de la rubrica y su efecto en el diseno

| Criterio | Peso |
|---|---|
| Comprension Transformer y del LLM | 25% |
| Funcionalidad del asistente de voz | 25% |
| Interfaz y experiencia de usuario | 15% |
| Calidad del codigo y buenas practicas | 15% |
| Informe tecnico | 10% |
| Sustentacion y demo en vivo | 10% |

El catalogo de herramientas (Tool Calling) **no aparece en la rubrica**; el enunciado lo
clasifica como opcional. Por eso se recorto de siete herramientas a tres, y ninguna
requiere OAuth. El tiempo liberado se traslada al modulo de exploracion y al pipeline,
que juntos valen el 50%.

## 3. Alcance y fases

### Dentro de alcance

- Pipeline completo: push-to-talk -> STT -> LLM -> TTS.
- GUI de escritorio CustomTkinter con cuatro estados visuales.
- Memoria conversacional con truncado por turnos.
- Tres herramientas via Tool Calling: telemetria, busqueda web, lanzador Kiosk.
- Modulo de exploracion del Transformer: script CLI y pestana en la GUI.
- Cuatro controles de sustentacion en la interfaz.

### Fuera de alcance (decidido, no pendiente)

- Gmail y Google Calendar. Motivo: OAuth de Google cuesta 2-3 dias y vale 0% de la nota.
- Vision de pantalla. Motivo: agrega un segundo proveedor de modelo y mas superficie de error.
- Resumen de YouTube. Motivo: mismo criterio que las anteriores.
- Wake word y transcripcion en streaming. Motivo: subsistemas completos sin peso en rubrica.
- Empaquetado como ejecutable. Se ejecuta con `python main.py` en un entorno virtual.

### Fases con fecha de corte

**Nucleo — cierra el 22 de agosto.** Protege el 65% de la rubrica.
Pipeline end-to-end, GUI con los cuatro estados, memoria, manejo de errores,
`exploration/transformer_lab.py` como script, README reproducible.

**Valor agregado — 23 al 25 de agosto, solo si el nucleo esta cerrado.**
En este orden: pestana Laboratorio, cuatro controles de sustentacion, tres herramientas.
Lo que no entre se descarta sin renegociar.

**Cierre — 26 y 27 de agosto, intocable.** Informe, video y ensayo. No se toca codigo.

Criterio de corte: si el 25 de agosto falta la pestana Laboratorio, la entrega cumple
todo lo obligatorio. Si el 25 falta el pipeline, no hay proyecto.

## 4. Arquitectura

```
┌──────────────┐   audio    ┌──────────────────────────┐
│  Microfono   ├───────────►│  Whisper large v3        │
│ (push-to-talk)│            │  Together AI  /v1/audio  │
└──────────────┘            └────────────┬─────────────┘
                                         │ texto
                                         ▼
┌──────────────┐  audio    ┌──────────────────────────┐
│  Altavoces   │◄──────────┤  edge-tts (local, gratis)│
└──────────────┘           └────────────▲─────────────┘
                                         │ texto final
                            ┌────────────┴─────────────┐
                            │  LLM  Together AI        │
                            │  Qwen2.5-72B-Instruct    │
                            │  Llama-3.3-70B-Instruct  │
                            └────────────▲─────────────┘
                                         │ tool_calls (JSON)
                            ┌────────────┴─────────────┐
                            │  Herramientas Python     │
                            │  telemetria · web · kiosk│
                            └──────────────────────────┘

        Todo coordinado por core/orchestrator.py (maquina de estados)
        Modulo de exploracion: independiente del pipeline
```

Proveedores y modelos exactos, para citar en el informe segun exige la seccion 11 del enunciado:

| Etapa | Proveedor | Modelo | Costo |
|---|---|---|---|
| STT | Together AI | `openai/whisper-large-v3` | $0.015 / min de audio |
| LLM | Together AI | `Qwen/Qwen2.5-72B-Instruct` (predeterminado) | por token |
| LLM alterno | Together AI | `meta-llama/Llama-3.3-70B-Instruct` | por token |
| TTS | Microsoft `edge-tts` | `es-MX-DaliaNeural` | sin costo |
| Exploracion (tokens) | Hugging Face | tokenizador de `Qwen/Qwen2.5-72B-Instruct`, sin pesos | sin costo |
| Exploracion (atencion) | Hugging Face | `dccuchile/bert-base-spanish-wwm-cased` (BETO) | sin costo |

`base_url = "https://api.together.xyz/v1"` con el SDK oficial de `openai`. La misma
clave `TOGETHER_API_KEY` sirve para STT y LLM, lo que reduce la gestion de credenciales
a una sola variable de entorno.

## 5. Modelo de concurrencia

**Decision: un hilo trabajador por interaccion, con clientes sincronos. Sin bucle
`asyncio` de larga vida.**

Esto se aparta de la sintesis inicial del equipo, que proponia `asyncio`. La razon:
Tkinter exige que su `mainloop` viva en el hilo principal y que ningun widget se
modifique desde otro hilo. Sostener un bucle `asyncio` en paralelo obliga a mantener
dos modelos de concurrencia conviviendo — `run_coroutine_threadsafe` en un sentido y
`root.after` en el otro. Es correcto, pero es donde un equipo sin experiencia previa
pierde dias depurando congelamientos de ventana, y choca con el requisito explicito de
que la aplicacion no se detenga abruptamente.

```
Hilo principal                Hilo trabajador (uno por turno, efimero)
──────────────                ────────────────────────────────────────
mainloop de Tk          ──►   1. grabar audio del microfono
root.after(0, cb)       ◄──   2. Whisper   (cliente sincrono)
root.after(0, cb)       ◄──   3. LLM       (cliente sincrono)
root.after(0, cb)       ◄──   4. edge-tts  (asyncio.run local y encapsulado)
```

`edge-tts` solo ofrece API asincrona, asi que se invoca con `asyncio.run()` **dentro**
del hilo trabajador. El bucle nace y muere en esa llamada; no persiste.

Regla invariante: **el unico canal de retorno hacia la GUI es `root.after`.** Ningun
hilo trabajador toca un widget directamente.

## 6. Modulos y responsabilidades

| Modulo | Responsabilidad unica | Depende de |
|---|---|---|
| `config.py` | claves desde `.env`, paleta pastel, constantes | — |
| `core/audio_capture.py` | microfono -> bytes en memoria | config |
| `core/stt_client.py` | bytes de audio -> texto | config |
| `core/llm_engine.py` | mensajes -> respuesta o peticion de tool | config, tools/manifest |
| `core/tts_engine.py` | texto -> audio reproducido | config |
| `core/memory.py` | historial, truncado por turnos, conteo | — |
| `core/orchestrator.py` | maquina de estados, hilo trabajador, despacho de tools | todos los core, tools |
| `tools/manifest.py` | esquemas JSON de las tres herramientas | — |
| `tools/system_skills.py` | implementacion de las tres herramientas | — |
| `gui/desktop_app.py` | widgets, estados visuales, controles | config, orchestrator |
| `exploration/transformer_lab.py` | tokenizacion, embeddings, atencion | — |
| `main.py` | punto de entrada | config, gui |

`core/memory.py` se separa de `llm_engine.py` deliberadamente: es lo que lee el indicador
de ventana de contexto de la GUI, y es la pieza mas facil de verificar sin tocar ninguna API.

## 7. Flujo de un turno

1. La usuaria mantiene presionado el boton (o la barra espaciadora). Estado -> **ESCUCHANDO**.
2. Se captura audio del microfono a memoria (`io.BytesIO`), sin archivo temporal en disco.
3. Al soltar, arranca el hilo trabajador. Estado -> **PENSANDO**.
4. El audio se envia a `openai/whisper-large-v3` con `language="es"`. Devuelve texto.
5. Si el texto viene vacio, se corta aqui con mensaje amable. Estado -> **ATENCION** -> reposo.
6. El texto se agrega a la memoria y se envia al LLM junto con el system prompt,
   el historial truncado y el manifest de herramientas.
7. Si el LLM pide una herramienta, el orquestador la ejecuta, agrega el resultado como
   mensaje de rol `tool` y vuelve a llamar al LLM. Maximo dos rondas de tool calling.
8. La respuesta final se agrega a la memoria. Estado -> **RESPONDIENDO**.
9. `edge-tts` sintetiza y reproduce. Estado -> reposo.

Limite de dos rondas de tool calling: evita un bucle infinito si el modelo insiste en
llamar herramientas. Al agotarse, responde con el texto que tenga.

## 8. Memoria conversacional

Lista de mensajes en formato OpenAI. El system prompt es fijo y nunca se descarta.
Se conservan los **ultimos 10 turnos** (usuario + asistente); al superarlos se descarta
el par mas antiguo.

El truncado por turnos —y no por tokens— se elige por ser predecible y verificable sin
llamar a ninguna API. El conteo aproximado de tokens se calcula aparte con el tokenizador
de Qwen, solo para alimentar el indicador visual.

Esto responde directamente la pregunta de sustentacion sobre exceder la ventana de
contexto: el mecanismo esta a la vista y se puede demostrar en vivo.

## 9. Tool calling

Tres herramientas, ninguna con OAuth ni credenciales de terceros:

| Herramienta | Libreria | Accion | Riesgo |
|---|---|---|---|
| `estado_laptop` | `psutil` | bateria, RAM y CPU en tono conversacional | ninguno, solo lectura |
| `buscar_web` | `duckduckgo-search` | consulta informacion actual | red saliente |
| `abrir_kiosk` | `subprocess` + MS Edge | abre una URL en pantalla completa | **ejecuta un proceso** |

`abrir_kiosk` es la unica superficie de riesgo real. Mitigacion: la URL se valida contra
una lista blanca de dominios definida en `config.py` antes de construir el comando, y el
comando se arma como lista de argumentos, nunca por concatenacion de cadena. El LLM no
ejecuta codigo: solo emite JSON que el orquestador interpreta.

## 10. Modulo de exploracion del Transformer

Es el criterio de mayor peso (25%) y tiene una limitacion que debe declararse de frente.

**El problema:** Qwen 2.5 72B corre en los servidores de Together AI por API. Un endpoint
HTTP no expone pesos de atencion. Es fisicamente imposible extraer una matriz de
self-attention del modelo de produccion.

**La solucion, en dos niveles:**

1. **Tokenizacion con el tokenizador real de Qwen.** `transformers` permite descargar el
   tokenizador sin los pesos del modelo: pesa pocos MB y no requiere GPU ni `torch`. Se
   muestran tokens e IDs de una frase en espanol del propio proyecto.
2. **Embeddings y self-attention con un modelo pequeno local.** Se usa
   `dccuchile/bert-base-spanish-wwm-cased` (BETO, ~110M parametros), entrenado en espanol
   y capaz de devolver `output_attentions=True`. Se muestran la forma del tensor de
   embeddings y un mapa de calor de una capa y cabeza concretas, guardado como PNG.
   Alternativa si BETO da problemas de descarga: `distilbert-base-multilingual-cased`.

En el informe se documenta explicitamente: *el modelo de produccion es un servicio remoto,
por lo que la inspeccion interna se realiza sobre un Transformer local de la misma familia
arquitectonica*. Convertir la limitacion en explicacion es preferible a esquivarla.

**Mitigacion de riesgo:** el nivel 1 no depende de `torch`; el nivel 2 si. Si `torch` no
instala en el interprete elegido, la tokenizacion sobrevive intacta y solo se replantea la
parte de atencion. Por eso la verificacion del entorno es la primera tarea del plan.

El script se ejecuta solo, sin la GUI, con un comando documentado en el README. La pestana
Laboratorio de la interfaz consume la misma logica sobre la ultima frase dicha.

## 11. Interfaz y estados

Tarjeta flotante de escritorio en CustomTkinter, modo claro.

Paleta: crema `#F9F9FB` de fondo, verde menta `#E8F5E9`, rosa palido `#FCE4EC`,
azul cielo `#E1F5FE`, durazno `#FFF3E0`, texto gris marengo `#37474F`.

Los cinco acentos son tintes Material de nivel 50 (green, pink, light-blue, orange).
Mantener ese nivel al anadir cualquier color nuevo: es lo que da coherencia visual.

**Correccion 2026-08-13.** La version original de esta seccion no asignaba color a
RESPONDIENDO ni a ATENCION, y el mapeo provisional los dejaba compartiendo rosa
palido. Eso incumple H-09, que exige distinguir los cuatro estados sin leer texto.
Se anade durazno `#FFF3E0` para ATENCION. Detectado por el Obrero durante T-03.

| Estado | Color | Senal visual | Forma |
|---|---|---|---|
| ESCUCHANDO | verde menta `#E8F5E9` | captura activa de microfono | circulo lleno, pulso lento |
| PENSANDO | azul cielo `#E1F5FE` | razonando o invocando herramientas | puntos en secuencia |
| RESPONDIENDO | rosa palido `#FCE4EC` | reproduciendo la voz | onda de audio ligera |
| ATENCION | durazno `#FFF3E0` | error, sin congelar la interfaz | triangulo con borde |

**El color no basta.** H-09 pide distinguirlos por color *y forma*: una persona con
daltonismo debe poder operar la aplicacion. La columna de forma no es decorativa.

**Controles de sustentacion** (fase de valor agregado). Cada uno responde una pregunta
guia de la seccion 12 del enunciado:

| Control | Pregunta que responde |
|---|---|
| Sliders de `temperature` y `top_p` | "Que pasa si cambias la temperatura o el top-p? Demuestralo" |
| Indicador de turnos y tokens en memoria | "Que pasaria si la conversacion excede la ventana de contexto?" |
| Visor del system prompt | "Como defines la personalidad? Muestra el system prompt" |
| Selector Qwen / Llama | "Comparacion de respuestas entre modelos" (valor agregado) |

## 12. Identidad del asistente

Voz femenina en espanol, tono calido y amigable, definida por system prompt documentado.
El prompt debe incluir una instruccion explicita de que el asistente declare ser una IA
cuando se le pregunte, y que sus respuestas pueden contener errores — lo exige la seccion
11 del enunciado sobre consideraciones eticas.

## 13. Manejo de errores

La maquina de estados incluye **ATENCION**, del que siempre se regresa a reposo. Ninguna
excepcion sube hasta el `mainloop` de Tkinter.

| Fallo | Respuesta al usuario |
|---|---|
| Microfono no disponible o sin permiso | mensaje claro, sugiere revisar el dispositivo |
| Sin conexion o timeout de API | avisa y ofrece reintentar |
| `TOGETHER_API_KEY` invalida o sin saldo | mensaje especifico; es el fallo mas probable en demo |
| Transcripcion vacia | "no te escuche bien, intenta de nuevo" |
| Respuesta vacia del LLM | reintento unico, luego mensaje |
| JSON de tool malformado | se ignora la tool y responde con texto |
| Fallo de `edge-tts` | muestra la respuesta en pantalla aunque no suene |

Ningun mensaje de error muestra trazas tecnicas ni fragmentos de la API key.

## 14. Seguridad de credenciales

- `TOGETHER_API_KEY` vive solo en `.env`, que `.gitignore` excluye desde el primer commit.
- `.env.example` lista los nombres de variables sin un solo valor real.
- Ninguna clave se imprime en logs, ni en mensajes de error, ni en la GUI.
- Antes de cada `push` se revisa que no haya secretos en el diff.
- El repositorio es **publico**: un secreto publicado no se recupera borrandolo despues.

## 15. Verificacion

**Gates deterministas** — corren sin APIs, sin microfono y sin red:

- truncado de memoria conversacional a 10 turnos
- validez de los esquemas JSON de `tools/manifest.py`
- parseo de `tool_calls` bien y mal formados
- las tres herramientas (telemetria y busqueda web se verifican; kiosk se verifica solo
  la construccion del comando y la lista blanca, sin lanzar el proceso)
- carga de configuracion con y sin variables presentes
- `python -m compileall`

**Verificacion humana** — vive en `.agents/TESTING.md`: calidad del audio capturado,
latencia percibida del turno completo, legibilidad de los estados de la GUI, y la prueba
de instalacion desde cero en otra maquina que exige el enunciado.

## 16. Riesgos conocidos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| `torch` sin wheel para Python 3.14.5 | bloquea el 25% de la rubrica | primera tarea del plan verifica el stack; si falla se fija Python 3.12 |
| Microfono o drivers de audio en Windows | bloquea el pipeline entero | se prueba en la primera tarea, antes de escribir codigo de producto |
| Congelamiento de la GUI | incumple requisito explicito | modelo de hilos de la seccion 5; regla invariante de `root.after` |
| Sin saldo en Together AI durante la demo | falla la sustentacion en vivo | verificar saldo la vispera; tener un video demo ya grabado |
| Alcance mayor que el tiempo | entrega incompleta | fases con fecha de corte de la seccion 3 |
| OneDrive reactivandose sobre `.git` | corrupcion del repositorio | riesgo dormido, el proceso no corre; no reactivar durante el proyecto |

## 17. Limitaciones a documentar en el informe

El enunciado exige documentar limitaciones conocidas. Las de este sistema:

- El modelo puede alucinar: afirmar con seguridad informacion incorrecta.
- Depende por completo de conexion a internet y de un proveedor externo.
- La inspeccion de self-attention no se hace sobre el modelo de produccion, por la
  limitacion tecnica explicada en la seccion 10.
- La memoria se pierde al cerrar la aplicacion; no hay persistencia entre sesiones.
- El truncado por turnos puede descartar contexto todavia relevante en conversaciones largas.
- La transcripcion degrada con ruido de fondo y acentos marcados.
- Los sesgos presentes en los datos de entrenamiento del modelo se trasladan a las respuestas.

---

## Registro de decisiones

| Decision | Alternativa descartada | Motivo |
|---|---|---|
| Tres herramientas sin OAuth | catalogo de siete con Gmail y Calendar | 0% de la rubrica contra 2-3 dias de trabajo |
| Push-to-talk | wake word, streaming continuo | robustez en demo de aula sobre vistosidad |
| Whisper large v3 | Nemotron 3.5 ASR streaming | precision en espanol; la diferencia de costo es menor a $1 en todo el proyecto |
| Hilos trabajadores | bucle `asyncio` persistente | evitar dos modelos de concurrencia conviviendo con Tkinter |
| Truncado por turnos | truncado por tokens | predecible y verificable sin llamar a la API |
| Exploracion en dos niveles | inspeccionar el modelo de produccion | tecnicamente imposible via API |
| Repositorio publico | privado con invitacion al docente | eleccion de la duena; simplifica compartir |
