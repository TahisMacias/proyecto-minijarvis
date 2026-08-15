# Cobertura de los 7 fallos previstos (T-12)

La seccion 13 del documento de diseno lista siete fallos que la aplicacion debe
atender con un mensaje propio, sin trazas tecnicas y sin quedarse trabada. Esta tabla
dice donde vive cada uno y como se comprobo.

Regla comun a los siete: el mensaje que ve la usuaria lo redacta el modulo que
conoce la causa, y el orquestador lo muestra tal cual. Cualquier excepcion que **no**
venga de un modulo de `core/` se reemplaza por un mensaje generico, para que una
traza tecnica no llegue nunca a la pantalla.

| # | Fallo | Donde se atiende | Mensaje a la usuaria | Como se verifico |
|---|---|---|---|---|
| 1 | Microfono no disponible o sin permiso | `core/audio_capture.py` -> `MicrofonoNoDisponible` | "No se encontro ningun microfono disponible. Revisa que haya un microfono conectado y que Windows le haya dado permiso..." | Se pidio el dispositivo inexistente numero 999: levanto el error tipado, no una traza de PortAudio. |
| 2 | Sin conexion o timeout de API | `core/stt_client.py` -> `SinConexionSTT`; `core/llm_engine.py` -> `SinConexionLLM` | "Revisa tu conexion a internet e intenta de nuevo." | Turno completo con el motor apuntando a un puerto cerrado (`127.0.0.1:9`): fallo de red **real**, no simulado. La aplicacion mostro el aviso y volvio a REPOSO. |
| 3 | `TOGETHER_API_KEY` invalida o sin saldo | `CredencialRechazadaSTT` y `CredencialRechazadaLLM` | "El servicio rechazo las credenciales. Verifica que TOGETHER_API_KEY... y que la cuenta tenga saldo." | Clientes falsos levantando `AuthenticationError`, `PermissionDeniedError` y `RateLimitError`. En Together, quedarse sin saldo llega como 429; por eso se agrupa con el limite de peticiones. |
| 4 | Transcripcion vacia | `core/orchestrator.py` | "No te escuche bien. Intenta de nuevo, por favor." | Pruebas con transcripcion vacia y con puros espacios. El segundo caso descubrio un defecto real: el texto en blanco pasaba como valido. |
| 5 | Respuesta vacia del LLM | `core/orchestrator.py`, reintento unico | "Me quede sin palabras con esa. Intenta preguntarme de otra forma." | Dos pruebas: con una vacia seguida de una buena, el reintento salva el turno; con dos vacias seguidas, se llama al modelo exactamente dos veces y luego se avisa. |
| 6 | JSON de tool malformado | `core/llm_engine.py` -> `interpretar_respuesta` | (sin mensaje: se ignora la herramienta y se responde con el texto disponible) | Cuatro pruebas de parseo: JSON roto, argumentos que no son objeto, una herramienta rota entre varias buenas, y argumentos vacios. |
| 7 | Fallo de `edge-tts` | `core/tts_engine.py` -> `ErrorDeTTS`, manejado aparte en el orquestador | "No se pudo generar la voz..." / "El sistema no pudo reproducir la respuesta hablada..." | Prueba dedicada: la respuesta ya se mostro y quedo en la memoria de la conversacion; solo falta el sonido. El turno **no** se pierde. |

## Lo que NO se cubre, y se dice de frente

- Si Together AI cambia el identificador de un modelo o lo saca del servicio
  compartido, la aplicacion avisa con el mensaje generico del fallo 2 o con el codigo
  de estado. No hay reintento automatico contra otro modelo. Es una decision: cambiar
  de modelo a espaldas de la usuaria haria que la demostracion mostrara algo distinto
  de lo que dice mostrar.
- Un microfono que funciona pero capta solo ruido no es un fallo detectable: produce
  una transcripcion equivocada, no vacia. Se atiende como conversacion normal.

## Comprobacion de que la ventana sobrevive a un fallo

En los seis caminos de fallo probados, la secuencia de estados termina siempre igual:

    ... -> ATENCION -> REPOSO

Nunca queda en ATENCION ni en PENSANDO. Esa es la invariante que impide el sintoma
mas dificil de diagnosticar en vivo: una aplicacion que no se cerro pero se quedo
muda para siempre.
