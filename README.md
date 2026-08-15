# Mini-JARVIS

Mini-JARVIS es un asistente conversacional por voz en espanol, desarrollado como
proyecto academico para la asignatura Redes Neuronales (Desarrollo de Software) de
CENESTUR. Funciona con push-to-talk: el usuario mantiene presionado un boton, habla,
y el asistente transcribe el audio, genera una respuesta con un modelo de lenguaje
(LLM) real y la reproduce por voz. El proyecto tambien incluye un modulo de
exploracion que evidencia, de forma didactica, como funcionan la tokenizacion, los
embeddings y el mecanismo de self-attention de la arquitectura Transformer.

> **Estado actual: el nucleo funciona de extremo a extremo.** El ciclo completo
> —hablar, transcribir, pensar y responder con voz— esta implementado y verificado.
> El tool calling (que Mini-JARVIS consulte la bateria, busque en la web o abra una
> pagina) es la fase siguiente y todavia no esta disponible.

## Requisitos

- **Python 3.14.5** (version verificada; el proyecto no se ha probado en otras versiones)
- Sistema operativo **Windows**
- Microfono funcional
- Conexion a internet (el STT y el LLM se ejecutan en la nube via Together AI)
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
3. El indicador de arriba dice en que va, por color **y por forma**:

   | Estado | Forma | Significado |
   |---|---|---|
   | Reposo | circulo punteado | listo para escucharte |
   | Escuchando | circulo que late | el microfono esta abierto |
   | Pensando | tres puntos | consultando al modelo |
   | Respondiendo | onda de audio | reproduciendo la voz |
   | Atencion | triangulo con `!` | algo no salio; ya volvio a reposo |

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

## Modelos y proveedores utilizados

| Etapa | Proveedor | Modelo | Costo |
|---|---|---|---|
| Transcripcion (STT) | Together AI | `openai/whisper-large-v3` | $0.015 / min de audio |
| LLM (predeterminado) | Together AI | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | por token |
| LLM (alterno) | Together AI | `Qwen/Qwen2.5-7B-Instruct-Turbo` | por token |
| Sintesis de voz (TTS) | Microsoft `edge-tts` | `es-MX-DaliaNeural` | sin costo |
| Exploracion (tokenizacion) | Hugging Face | tokenizador de `Qwen/Qwen2.5-7B-Instruct`, sin pesos | sin costo |
| Exploracion (embeddings y atencion) | Hugging Face | `dccuchile/bert-base-spanish-wwm-cased` (BETO) | sin costo |

Los modelos llevan el sufijo `-Turbo` porque son los que Together AI sirve de forma
compartida. Sus versiones sin ese sufijo aparecen en el catalogo pero **no responden**
sin contratar un endpoint dedicado: devuelven `HTTP 400 non-serverless model`.

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
core/orchestrator.py           maquina de estados y el hilo de cada turno
gui/desktop_app.py             la ventana
main.py                        punto de entrada
exploration/transformer_lab.py laboratorio del Transformer (independiente)
tests/                         pruebas deterministas
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
