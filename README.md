# Mini-JARVIS

**La asistente se llama Elena.** Mini-JARVIS es el nombre del proyecto; Elena es a
quien se le habla: se le dice "hola Elena" y responde a su nombre. La seccion 4 del
enunciado lo permite explicitamente ("puede ser una replica cercana a JARVIS o una
identidad propia, siempre que quede definida mediante un system prompt claro y
documentado"). Su identidad vive en `SYSTEM_PROMPT`, en `core/llm_engine.py`, y su
nombre en una sola constante: `NOMBRE_ASISTENTE`, en `config.py`.

Mini-JARVIS es un asistente conversacional por voz en espanol, desarrollado como
proyecto academico para la asignatura Redes Neuronales (Desarrollo de Software) de
CENESTUR. Funciona con push-to-talk: el usuario mantiene presionado un boton, habla,
y el asistente transcribe el audio, genera una respuesta con un modelo de lenguaje
(LLM) real y la reproduce por voz. El proyecto tambien incluye un modulo de
exploracion que evidencia, de forma didactica, como funcionan la tokenizacion, los
embeddings y el mecanismo de self-attention de la arquitectura Transformer.

> **Estado actual: completo y verificado.** El ciclo entero —hablar, transcribir,
> pensar y responder con voz— funciona, con memoria entre turnos. Mini-JARVIS ademas
> **usa diez herramientas**: resuelve cuentas exactas, dice la hora, consulta el
> clima y el estado de la laptop, busca en internet, abre paginas de una lista
> blanca, sube y baja el volumen y el brillo, abre carpetas y pone musica en
> YouTube. La ventana muestra a la vez la
> conversacion y el analisis del Transformer de la ultima frase.

## Requisitos

- **Python 3.14.5** (version verificada; el proyecto no se ha probado en otras versiones)
- Sistema operativo **Windows**
- Microfono funcional
- Conexion a internet para el modo normal. **Tambien funciona sin ella**: ver
  "Modo sin internet" mas abajo.
- Una clave de API de [Together AI](https://api.together.xyz)

## Instalacion

### 1. Clonar el repositorio y ubicarse en su carpeta

```powershell
git clone https://github.com/TahisMacias/proyecto-minijarvis.git
cd proyecto-minijarvis
```

### 2. Crear y activar el entorno virtual (PowerShell, Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecucion del script de activacion por la politica de
ejecucion, habilitala para el usuario actual antes de reintentar:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 3. Instalar las dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar la clave de API

Copia el archivo de ejemplo y coloca tu clave real dentro de `.env` (este archivo
nunca se sube al repositorio, ya esta excluido en `.gitignore`):

```powershell
Copy-Item .env.example .env
```

Luego edita `.env` y reemplaza el valor vacio de `TOGETHER_API_KEY` por tu clave,
obtenida en https://api.together.xyz.

## Ejecucion

**La forma comoda: doble clic en `Iniciar Mini-JARVIS.bat`**, en la carpeta del
proyecto. Comprueba que el entorno virtual y el archivo `.env` esten en su sitio,
explica que falta si falta algo, y abre la aplicacion. Se le puede crear un acceso
directo en el escritorio (clic derecho > Enviar a > Escritorio).

Deja abierta la ventana negra que aparece detras: si se cierra, se cierra tambien el
asistente.

La forma manual, con el entorno virtual activado:

```powershell
python main.py
```

Ejecutar por separado el modulo de exploracion del Transformer (tokenizacion,
embeddings y self-attention), sin necesidad de abrir la GUI ni usar el microfono:

```powershell
python -m exploration.transformer_lab
```

La primera ejecucion descarga de Hugging Face el tokenizador y los pesos de BETO
(unos cientos de MB) y tarda varios minutos. Las siguientes usan la cache local y
funcionan incluso sin conexion. Deja el PNG del mapa de atencion en
`exploration/mapa_atencion.png`.

### Como se usa la aplicacion

1. **Manten presionado** el boton (o la **barra espaciadora**) mientras hablas.
2. Sueltalo al terminar. La respuesta aparece en el panel y se escucha en voz alta.
3. La pieza grande de la izquierda dice en que va, por color **y por forma**:

   | Estado | Forma | Significado |
   |---|---|---|
   | Reposo | circulo punteado | listo para escucharte |
   | Escuchando | circulo que late | el microfono esta abierto |
   | Pensando | tres puntos | consultando al modelo |
   | Respondiendo | onda de audio | reproduciendo la voz |
   | Atencion | triangulo con `!` | algo no salio; ya volvio a reposo |

4. Debajo de la conversacion estan los controles de la sustentacion: temperatura,
   `top_p`, selector de modelo en caliente e indicador de memoria.
5. Mas abajo, el laboratorio analiza cada frase que dices. Tres botones abren el
   system prompt, la tabla de tokens y el mapa de atencion.

### Comprobaciones sueltas

Verificar el microfono (graba 3 segundos y reporta lo capturado):

```powershell
python -m core.audio_capture
```

Verificar la voz (sintetiza una frase y la reproduce):

```powershell
python -m core.tts_engine
```

Ejecutar la bateria de pruebas (no necesita microfono, red ni saldo de API):

```powershell
pytest
```

## Modo sin internet

Mini-JARVIS funciona con el wifi apagado. La nube sigue siendo el camino normal porque
responde mucho mejor; cuando se cae la conexion, la aplicacion **lo nota sola** y pasa
a tres modelos que viven en esta maquina. No hay que tocar ningun ajuste.

**Antes hay que descargarlos, una vez y con internet:**

```powershell
python -m core.modo_local
```

Son unos 700 MB y tarda un par de minutos. Hazlo con tiempo: si no, la primera vez que
se caiga la red habra que descargarlos justo en ese momento.

Que cambia cuando entra el respaldo, medido en una laptop sin tarjeta grafica:

| Pieza | Con internet | Sin internet |
|---|---|---|
| Oir | Whisper en la nube, ~2 s | Whisper local (`base`), ~2 s |
| Pensar | Qwen3.8, billones de parametros, 1-3 s | Qwen2.5-0.5B, 494 millones, ~4 palabras/s |
| Hablar | voz neuronal de Microsoft | voz de Windows, mas robotica |
| Herramientas | las diez | ninguna |

**La diferencia se nota y la aplicacion no la disimula**: cuando el respaldo entra, lo
dice en la conversacion y aparece un aviso ambar arriba a la derecha.

**Cuenta con que se equivoque.** Preguntandole dos veces seguidas la capital de Ecuador,
el modelo local contesto "Quito" una vez y "Santo Domingo" la otra. No es un fallo del
programa: es lo que da un modelo de 494 millones de parametros. Sirve para que la
aplicacion siga viva sin conexion, no para confiar en lo que dice.

Los modelos locales se cargan **en segundo plano nada mas abrir la aplicacion**, para
que el cambio sea instantaneo si se cae la red. Tarda unos 18 segundos y no bloquea
nada. Sin ese precalentado, el primer turno sin internet tardaba mas de un minuto.

Dos cosas que el respaldo NO hace, a proposito:

- **No se activa si la clave de API es invalida o la cuenta se quedo sin saldo.** Solo
  ante falta de red. Cambiar al modelo pequeno ante un problema de credenciales
  esconderia la causa real.
- **No usa herramientas.** Un modelo de 494 millones de parametros no elige bien entre
  diez herramientas, y una llamada mal elegida es peor que ninguna.

El modulo de exploracion del Transformer **siempre** funciona sin internet, porque BETO
se ejecuta en local desde el principio.

## Modelos y proveedores utilizados

| Etapa | Proveedor | Modelo | Costo |
|---|---|---|---|
| Transcripcion (STT) | Together AI | `openai/whisper-large-v3` | $0.0015 / min de audio |
| LLM (predeterminado) | Together AI | `Qwen/Qwen3.8-2.4T-A95B` | $2.50 entrada / $6.25 salida por millon de tokens |
| LLM (alterno) | Together AI | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | $1.04 entrada / $1.04 salida por millon de tokens |
| Sintesis de voz (TTS) | Microsoft `edge-tts` | `es-AR-ElenaNeural` | sin costo |
| STT sin internet | local | `faster-whisper base` | sin costo |
| LLM sin internet | local | `Qwen/Qwen2.5-0.5B-Instruct` | sin costo |
| Voz sin internet | Windows SAPI | voz `es-ES` instalada | sin costo |
| Exploracion (tokenizacion) | Hugging Face | tokenizador de `Qwen/Qwen2.5-7B-Instruct`, sin pesos | sin costo |
| Exploracion (embeddings y atencion) | Hugging Face | `dccuchile/bert-base-spanish-wwm-cased` (BETO) | sin costo |

Estos dos modelos de lenguaje **se eligieron probandolos uno por uno contra la API
real**, no leyendo el catalogo. Aparecer en `GET /v1/models` no significa estar
disponible: de los 169 modelos de chat que lista Together, **solo 20 responden**. El
resto devuelve `HTTP 400 non-serverless model`, porque estan en el catalogo pero no en
el servicio compartido. El campo `running` del catalogo tampoco sirve: viene en `false`
para todos.

**Y la disponibilidad cambia con el tiempo.** El alterno era
`Qwen/Qwen2.5-7B-Instruct-Turbo`, que funcionaba el 14 de agosto y devolvia `HTTP 503`
tres dias despues. Si algun modelo deja de responder, hay que volver a probar el
catalogo y actualizar `config.py`.

El predeterminado es un modelo de razonamiento: escribe un borrador interno antes de
contestar, y por eso gasta mas tokens de salida. El alterno es de otra familia y no
razona antes de responder, asi que contesta mas rapido y mas escueto. El contraste se
nota en vivo y es lo que hace util el selector durante la sustentacion.

**Aviso sobre la temperatura:** el slider llega hasta 1.4 y no mas. Midiendo contra la
API, a partir de 1.5 el modelo de razonamiento se atasca unos 100 segundos en dos de
cada tres intentos.

La fuente unica de verdad de estos identificadores es [`config.py`](config.py); si
alguna vez esta tabla y ese archivo no coinciden, manda `config.py`.

Detalle completo de la arquitectura y las decisiones de diseno en
`docs/specs/2026-08-13-mini-jarvis-design.md`.

## Estructura del proyecto

```
Iniciar Mini-JARVIS.bat        lanzador para abrir la app con doble clic
config.py                      fuente unica de configuracion y credenciales
core/memory.py                 historial de la conversacion y su truncado
core/audio_capture.py          microfono -> WAV en memoria
core/stt_client.py             WAV -> texto (Whisper)
core/llm_engine.py             mensajes -> respuesta del modelo
core/tts_engine.py             texto -> voz reproducida
core/modo_local.py             respaldo sin internet: oir, pensar y hablar en local
core/orchestrator.py           maquina de estados y el hilo de cada turno
tools/manifest.py              lo que el modelo lee para saber que puede pedir
tools/system_skills.py         lo que hacen las herramientas (sin eval, lista blanca)
gui/desktop_app.py             la ventana
main.py                        punto de entrada
exploration/transformer_lab.py laboratorio del Transformer (independiente)
tests/                         pruebas deterministas (133)
```

## Si algo falla

| Sintoma | Que revisar |
|---|---|
| `Falta la variable TOGETHER_API_KEY` | El archivo `.env` no existe o esta vacio. Repite el paso 4. |
| `No se encontro ningun microfono disponible` | Conecta un microfono y dale permiso en Configuracion > Privacidad > Microfono. |
| "El servicio rechazo las credenciales" | La clave es incorrecta o la cuenta se quedo sin saldo. |
| "Revisa tu conexion a internet" | Sin red. La aplicacion no se rompe: vuelve sola a reposo. |
| La respuesta se ve pero no se escucha | Revisa el volumen y el dispositivo de salida; el texto no se pierde. |
| `Activate.ps1 no se puede cargar` | Ejecuta el `Set-ExecutionPolicy` del paso 2. |

## Aviso importante

Mini-JARVIS utiliza un modelo de lenguaje (IA). Sus respuestas pueden contener
errores o informacion incorrecta (alucinaciones). No debe usarse como fuente unica
de informacion critica.
