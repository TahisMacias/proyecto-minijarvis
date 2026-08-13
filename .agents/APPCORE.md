# APPCORE - Mini-JARVIS

Verified: 2026-08-13 (pre-primer-commit; sin codigo de producto todavia)

## Purpose and users

- Problema: construir un asistente conversacional por voz que demuestre de forma
  aplicada la arquitectura Transformer, el manejo de contexto y el Tool Calling.
  Es el proyecto integrador de **Redes Neuronales**, Desarrollo de Software, CENESTUR.
- Usuarios: el equipo (demo en vivo) y el docente evaluador. No es software de produccion.
- Non-goals:
  - Entrenar un LLM desde cero (el PDF lo excluye explicitamente).
  - Simular respuestas con reglas `if/else` o texto hardcodeado (prohibido, seccion 6).
  - Multiusuario, persistencia en base de datos, despliegue en la nube.

## Stable constraints and invariants

- El LLM debe ser un modelo preentrenado **real**, via API o local.
- Ninguna credencial en el repositorio. Solo variables de entorno y `.env` ignorado.
- El proyecto debe correr en **otra maquina** siguiendo unicamente el README.
- Historial de commits progresivo que refleje avance del equipo.
- Debe existir un **modulo de exploracion** que evidencie tokenizacion y self-attention.
  Es el criterio de mayor peso de la rubrica (25%).
- La UI debe comunicar estado: escuchando / pensando / hablando / error.
- Memoria conversacional de al menos los ultimos turnos.
- Manejo de errores sin que la app se caiga.

## Architecture map

Estructura objetivo acordada por el equipo (aun **no implementada** — es el destino, no el estado):

- `main.py`: punto de entrada de la app de escritorio.
- `config.py`: paleta pastel, constantes y carga de API keys desde `.env`.
- `core/stt_client.py`: captura de microfono y transcripcion (Whisper API).
- `core/llm_engine.py`: cliente Together AI, system prompt e historial conversacional.
- `core/tts_engine.py`: sintesis de voz femenina con `edge-tts`.
- `core/orchestrator.py`: maquina de estados asincrona (escuchando/pensando/hablando/error).
- `tools/manifest.py`: esquemas JSON declarados para el Tool Calling.
- `tools/system_skills.py`: implementacion de las habilidades. **Superficie de riesgo**:
  ejecuta `subprocess`, envia correos y toma capturas de pantalla.
- `gui/desktop_app.py`: ventana CustomTkinter.
- `exploration/transformer_lab.py`: script de tokenizacion, embeddings y self-attention.
- `requirements.txt`, `.env.example`, `README.md`.

## Interfaces and protocols

- **Pipeline**: microfono -> STT -> LLM (+ tool calling) -> TTS -> altavoces,
  coordinado por el orquestador, que ademas mantiene estado y memoria.
- **LLM**: SDK oficial de `openai` apuntando a `base_url="https://api.together.xyz/v1"`.
  Modelo objetivo: `Qwen/Qwen2.5-72B-Instruct` o `meta-llama/Llama-3.3-70B-Instruct`.
- **Tool Calling**: el LLM devuelve JSON; el orquestador despacha a la funcion Python
  correspondiente y devuelve el resultado al modelo. El LLM nunca ejecuta codigo directo.
- **Autoridad**: las API keys viven solo en `.env` en la maquina local. Ningun secreto
  se envia a la GUI ni se escribe en logs.

## External systems

- **Together AI**: inferencia del LLM. Requiere `TOGETHER_API_KEY`.
- **Whisper API**: transcripcion. Requiere clave propia segun proveedor elegido.
- **edge-tts**: sintesis de voz. Servicio de Microsoft, sin clave.
- **Google (Gmail / Calendar)**: opcional, herramientas de Tool Calling. OAuth pendiente
  de decidir; es la integracion mas cara en tiempo. Ver riesgos en el plan activo.

## Documentos fuente (autoridad academica)

- `Proyecto_MiniJARVIS.pdf`: enunciado oficial, requisitos y rubrica. Manda sobre todo lo demas.
- `Sintesis del proyecto.md`: decisiones de diseno tomadas por el equipo.
