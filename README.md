# Mini-JARVIS

Mini-JARVIS es un asistente conversacional por voz en espanol, desarrollado como
proyecto academico para la asignatura Redes Neuronales (Desarrollo de Software) de
CENESTUR. Funciona con push-to-talk: el usuario mantiene presionado un boton, habla,
y el asistente transcribe el audio, genera una respuesta con un modelo de lenguaje
(LLM) real y la reproduce por voz. El proyecto tambien incluye un modulo de
exploracion que evidencia, de forma didactica, como funcionan la tokenizacion, los
embeddings y el mecanismo de self-attention de la arquitectura Transformer.

> **Estado actual del repositorio: esqueleto inicial.** Todavia no existe codigo de
> aplicacion (`core/`, `tools/`, `gui/`, `exploration/` solo contienen paquetes
> Python vacios). `main.py` aun no existe. Esta seccion se actualizara a medida que
> se implementen las tareas del plan. Por ahora, este README documenta como sera la
> instalacion y ejecucion una vez que el codigo este implementado.

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

> Los comandos de esta seccion describen el uso previsto. `main.py` y
> `exploration/transformer_lab.py` todavia no estan implementados en este
> repositorio; ejecutarlos hoy producira un error de "modulo no encontrado".

Iniciar la aplicacion (GUI de escritorio):

```powershell
python main.py
```

Ejecutar por separado el modulo de exploracion del Transformer (tokenizacion,
embeddings y self-attention), sin necesidad de abrir la GUI ni usar el microfono:

```powershell
python -m exploration.transformer_lab
```

## Modelos y proveedores utilizados

| Etapa | Proveedor | Modelo | Costo |
|---|---|---|---|
| Transcripcion (STT) | Together AI | `openai/whisper-large-v3` | $0.015 / min de audio |
| LLM (predeterminado) | Together AI | `Qwen/Qwen2.5-72B-Instruct` | por token |
| LLM (alterno) | Together AI | `meta-llama/Llama-3.3-70B-Instruct` | por token |
| Sintesis de voz (TTS) | Microsoft `edge-tts` | `es-MX-DaliaNeural` | sin costo |
| Exploracion (tokenizacion) | Hugging Face | tokenizador de `Qwen/Qwen2.5-72B-Instruct`, sin pesos | sin costo |
| Exploracion (embeddings y atencion) | Hugging Face | `dccuchile/bert-base-spanish-wwm-cased` (BETO) | sin costo |

Detalle completo de la arquitectura y las decisiones de diseno en
`docs/specs/2026-08-13-mini-jarvis-design.md`.

## Aviso importante

Mini-JARVIS utiliza un modelo de lenguaje (IA). Sus respuestas pueden contener
errores o informacion incorrecta (alucinaciones). No debe usarse como fuente unica
de informacion critica.
