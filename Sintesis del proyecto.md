> # ⚠️ DOCUMENTO HISTORICO — SUPERADO. NO CITAR EN EL INFORME NI EN LA SUSTENTACION.
>
> Esta es la sintesis que el equipo escribio **antes de construir nada**, el 13 de
> agosto de 2026. Se conserva porque muestra de donde partio el proyecto, pero
> **varias de sus decisiones no sobrevivieron al contacto con la realidad** y hoy
> contradicen a la aplicacion que existe.
>
> **La verdad vigente esta, en este orden:** `config.py` (identificadores y
> constantes), `README.md` (como se instala y que modelos usa) y
> `docs/specs/2026-08-13-mini-jarvis-design.md` (arquitectura y decisiones, con sus
> propias correcciones marcadas).
>
> ## Lo que este documento dice y ya no es cierto
>
> | Dice aqui | Realidad, y por que cambio |
> |---|---|
> | LLM `Qwen2.5-72B-Instruct` o `Llama-3.3-70B-Instruct` (seccion 2) | **Esta cuenta no puede usar ninguno de los dos.** Devuelven `HTTP 400 non-serverless`. Se probaron 26 identificadores uno por uno; hoy corre `Qwen/Qwen3.8-2.4T-A95B` con `Qwen/Qwen2.5-7B-Instruct-Turbo` de alterno. |
> | Orquestacion con `asyncio` (seccion 2) | **Descartado a proposito.** Tkinter exige su bucle en el hilo principal; sostener un bucle `asyncio` en paralelo es donde se pierden dias depurando ventanas congeladas. Se usa **un hilo trabajador efimero por turno**. Ver seccion 5 del documento de diseno. |
> | 7 herramientas: Kiosk, Gmail, Calendar, Vision de pantalla, Busqueda web, Resumen de YouTube, Telemetria (seccion 4) | **Son 3, y ninguna esta construida todavia.** T-15 planea `estado_laptop`, `buscar_web` y `abrir_kiosk`, mas una cuarta (`calcular`) que pidio la duena. Gmail, Calendar, Vision y YouTube se descartaron por costo en tiempo: OAuth era la integracion mas cara del plan. |
> | PENSANDO en "lavanda/azul cielo" (seccion 3) | Es **azul cielo** `#E1F5FE`, con borde saturado `#0277BD`. Cada estado tiene un color y una forma propios; que dos compartan color es NO APTO por H-09. |
> | Carpeta raiz `mini_jarvis/` (seccion 5) | **Nunca existio.** Los modulos viven en la raiz del repositorio (`core/`, `gui/`, `exploration/`). Ese nombre fantasma sobrevivio en el comando del gate de `AGENTS.md` hasta la auditoria del 14 de agosto, donde fallaba en silencio devolviendo exit 0. |
>
> Marcado como superado el 2026-08-17, cerrando un hallazgo abierto desde el
> 2026-08-14 en `.agents/CURRENT.md`.

---

Aquí tienes la síntesis final, completa y actualizada del proyecto **Mini-JARVIS**, incorporando la decisión definitiva de arquitectura de software, su interfaz de escritorio y todos los requisitos acordados.

## **1\. Visión General e Identidad del Proyecto**

> * **Propósito Académico:** Proyecto integrador de la asignatura *Redes Neuronales* (Carrera de Desarrollo de Software, CENESTUR) para diseñar e implementar un pipeline conversacional por voz (STT \\rightarrow LLM \\rightarrow TTS) que demuestre de forma aplicada la arquitectura Transformer, el manejo de contexto e interacción mediante herramientas (*Tool Calling*).  
> * **Formato de Presentación y Despliegue:** **Aplicación de Escritorio Nativa en Python** construida con **CustomTkinter**. Se ejecutará directamente mediante script en un entorno virtual (python main.py), lo que otorga acceso nativo al micrófono, altavoces, capturas de pantalla y ejecución de comandos sin lidiar con restricciones de navegador ni compilaciones complejas.  
> * **Identidad Visual (Pastel & Amigable):**  
  * **Estética:** Interfaz limpia, clara y acogedora en modo claro. Se descarta la estética oscura o *cyberpunk* morada.  
  * **Paleta de Colores:** Crema suave de fondo (\#F9F9FB), verde menta (\#E8F5E9), rosa pálido (\#FCE4EC), azul cielo (\#E1F5FE) y texto gris marengo (\#37474F).  
> * **Identidad Sonora:** Voz femenina en español, con tono cálido, fluido y amigable.

## **2\. Arquitectura del Sistema (Centrada en Together AI)**

Para maximizar el rendimiento en la laptop de la exposición, todo el procesamiento pesado de lenguaje se canalizará a través de la infraestructura de **Together AI**, logrando respuestas en tiempo real con cero carga local de GPU/RAM.  
 `┌────────────────┐      Audio      ┌───────────────────┐`  
 `│   Micrófono    ├────────────────►│ Whisper API (STT) │`  
 `└────────────────┘                 └─────────┬─────────┘`  
                                              `│ Texto`  
                                              `▼`  
 `┌────────────────┐   Respuesta TTS ┌───────────────────┐`  
 `│   Altavoces    │◄────────────────┤   edge-tts (TTS)  │`  
 `└────────────────┘                 └─────────▲─────────┘`  
                                              `│ Texto final`  
                                              `│`  
                                    `┌─────────┴─────────┐`  
                                    `│ Together AI (LLM) │`  
                                    `│ Qwen 2.5 72B /    │`  
                                    `│ Llama 3.3 70B     │`  
                                    `└─────────▲─────────┘`  
                                              `│`  
                                   `[ Tool Calling / JSON ]`  
                                              `│`  
                                    `┌─────────┴─────────┐`  
                                    `│ Herramientas Py   │`  
                                    `│ (Gmail, Screen,   │`  
                                    `│  Kiosk, Calendar) │`  
                                    `└───────────────────┘`

> * **LLM (Cerebro Central):** **Together AI API** con **Qwen/Qwen2.5-72B-Instruct** o **meta-llama/Llama-3.3-70B-Instruct**. Su tamaño de 70B+ parámetros garantiza un seguimiento de instrucciones impecable en español y una ejecución de *Tool Calling* sin fallos de sintaxis JSON.  
> * **STT (Voz a Texto):** API de Whisper procesando la captura de audio enviada desde memoria (io.BytesIO).  
> * **TTS (Texto a Voz):** Librería **edge-tts** configurada con voz femenina neuronal (ej. es-MX-DaliaNeural o es-ES-ElviraNeural).  
> * **Orquestación:** Código asíncrono con asyncio en Python, utilizando la SDK oficial de openai mediante el endpoint base\_url="\[https://api.together.xyz/v1\](https://api.together.xyz/v1)".

## **3\. Interfaz de Usuario y Experiencia de Escritorio (UI/UX)**

La aplicación se presentará como una **tarjeta flotante de escritorio** diseñada con CustomTkinter, ofreciendo retroalimentación visual clara según el estado del sistema:  
 `┌────────────────────────────────────────────────────────┐`  
 `│  🌸 Mini-JARVIS                                 [ - X ]│`  
 `├────────────────────────────────────────────────────────┤`  
 `│                                                        │`  
 `│                   (  ◕   ‿   ◕  )                       │`  
 `│              [ Indicador Pastel Animado ]               │`  
 `│                                                        │`  
 `│                   Estado: Escuchando...                │`  
 `│        "¿En qué puedo ayudarte el día de hoy?"         │`  
 `│                                                        │`  
 `├────────────────────────────────────────────────────────┤`  
 `│ [ Panel de conversación en tarjeta rosa pálido ]       │`  
 `└────────────────────────────────────────────────────────┘`

### **Máquina de Estados Visuales**

> 1. 🌸 **\[ ESCUCHANDO \]**: Indicador verde menta suave indicando captura activa de micrófono.  
> 2. 💭 **\[ PENSANDO \]**: Animación en lavanda/azul cielo mientras el modelo razona o invoca herramientas.  
> 3. 🗣️ **\[ RESPONDIENDO \]**: Animación de onda de audio ligera al reproducir la voz femenina.  
> 4. ⚠️ **\[ ATENCIÓN \]**: Notificaciones de error amigables sin interrumpir o congelar la interfaz.

## **4\. Catálogo de Habilidades y Herramientas (*Tool Calling*)**

Al recibir una petición de voz, el modelo de 70B+ evaluará el contexto y llamará autónomamente a la función de Python correspondiente:

| Habilidad | Herramienta / Librería | Descripción de la Acción |
| :---- | :---- | :---- |
| **Lanzador Kiosk WebApp** | subprocess \+ MS Edge | Abre aplicaciones o páginas web en modo pantalla completa (--kiosk). |
| **Gmail** | smtplib / Google API | Redacta y envía correos electrónicos en formato estructurado. |
| **Google Calendar** | Google Calendar API | Agenda eventos y citas calculando la fecha/hora actual del sistema. |
| **Visión de Pantalla** | pyautogui \+ VLM / Gemini Flash | Toma una captura de pantalla e interpreta gráficos, código o archivos abiertos. |
| **Búsqueda Web** | duckduckgo-search | Consulta información y noticias actualizadas en tiempo real. |
| **Resumen YouTube** | youtube-transcript-api | Descarga la transcripción de un video y genera un resumen conciso. |
| **Telemetría de la Laptop** | psutil | Reporta estado de batería, memoria RAM y CPU en un tono cálido y conversacional. |

## **5\. Estructura Modular del Proyecto**

Organización limpia del repositorio para garantizar un mantenimiento sencillo y desacoplado:  
`mini_jarvis/`  
`├── config.py              # Variables globales, colores pastel y API Keys desde .env`  
`├── core/`  
`│   ├── stt_client.py      # Captura de audio del micrófono y llamada a Whisper API`  
`│   ├── llm_engine.py      # Cliente Together AI, System Prompt e historial conversacional`  
`│   ├── tts_engine.py      # Generación y reproducción de voz femenina con edge-tts`  
`│   └── orchestrator.py    # Máquina de estados asíncrona (Escuchando/Pensando/Hablando)`  
`├── tools/`  
`│   ├── manifest.py        # Declaración de esquemas JSON para el Tool Calling de Qwen`  
`│   └── system_skills.py   # Implementación en Python de las habilidades (Gmail, Kiosk, etc.)`  
`├── gui/`  
`│   └── desktop_app.py     # Ventana CustomTkinter con paleta pastel y componentes`  
`├── exploration/`  
`│   └── transformer_lab.py # Script de demostración técnica (Tokenización y Atención)`  
`├── main.py                # Punto de entrada de la aplicación de escritorio`  
`├── requirements.txt       # Librerías necesarias para ejecutar el proyecto`  
`└── .env                   # Archivo protegido con las claves API (ignorado en Git)`

## **6\. Requisitos Académicos y Evaluación (Rúbrica)**

Para asegurar la máxima puntuación en la entrega y sustentación del proyecto:

> 1. **Módulo de Exploración del Transformer:** Script independiente (exploration/transformer\_lab.py) con tiktoken y un modelo pequeño de Hugging Face para ilustrar el proceso de tokenización, *embeddings* y extracción de la matriz de *self-attention*.  
> 2. **Repositorio Git:** Historial de *commits* progresivos que reflejen el trabajo del equipo, con archivo .env fuera del control de versiones.  
> 3. **Informe Técnico (4 a 8 páginas):** Documento formal con diagramas de arquitectura, decisiones de diseño, fundamentación teórica del Transformer y limitaciones del sistema.  
> 4. **Video Demostrativo (2 a 4 minutos):** Grabación ágil que exhiba el funcionamiento de la app de escritorio, la voz femenina, la interfaz pastel y la ejecución de *tools*.  
> 5. **Sustentación Oral:** Demostración en vivo respondiendo preguntas sobre la personalidad del asistente vía *prompting*, ajuste de hiperparámetros (temperatura, top-p) y funcionamiento interno de las capas de atención.