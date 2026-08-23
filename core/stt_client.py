"""Cliente de transcripcion de voz a texto (tarea T-06).

Toma el WAV en memoria que produce `core/audio_capture.py` y devuelve lo que la
usuaria dijo, en texto.

QUE PASA POR DEBAJO: el audio se sube a `openai/whisper-large-v3` alojado en Together
AI. Whisper es un modelo de reconocimiento de voz entrenado sobre cientos de miles de
horas de audio en decenas de idiomas. Se le pasa `language="es"` de forma explicita
en lugar de dejar que adivine: el modelo detecta el idioma solo, pero con audio corto,
ruido de fondo o una sola palabra puede equivocarse y transcribir espanol como si
fuera portugues o italiano. Fijar el idioma elimina esa clase entera de fallos.

SE USA EL CLIENTE DE `openai` CONTRA TOGETHER AI, no contra OpenAI: Together expone
una API compatible, asi que basta cambiarle la `base_url`. Eso ahorra escribir un
cliente HTTP propio y permite cambiar de proveedor tocando una constante.

UNA TRANSCRIPCION VACIA NO ES UN ERROR. Si la usuaria presiono el boton sin hablar,
o solo se grabo ruido, Whisper devuelve una cadena vacia y eso es una respuesta
legitima del sistema: el orquestador lo trata como "no te escuche bien" y vuelve a
reposo (seccion 13 del diseno). Levantar una excepcion ahi obligaria a tratar como
fallo algo que ocurre todos los dias.
"""

from __future__ import annotations

import io

import openai

from config import IDIOMA_STT, MODELO_STT, TOGETHER_API_KEY, TOGETHER_BASE_URL


# --- Errores tipados --------------------------------------------------------

class ErrorDeSTT(RuntimeError):
    """Base de los fallos de transcripcion. La GUI atrapa esta."""


class SinConexionSTT(ErrorDeSTT):
    """No se pudo llegar al servidor: sin internet, DNS caido o timeout."""


class CredencialRechazadaSTT(ErrorDeSTT):
    """La clave de API es invalida, esta vencida o la cuenta se quedo sin saldo."""


class TranscripcionFallida(ErrorDeSTT):
    """El servidor respondio, pero con un error o con algo que no sabemos leer."""


# Tiempo maximo de espera de una transcripcion. Un turno de voz de la demo dura
# segundos; si a los 60 no hubo respuesta, algo va mal y es mejor avisar que dejar
# la interfaz "pensando" indefinidamente.
TIMEOUT_SEGUNDOS = 60


def _sin_credenciales(texto: str) -> str:
    """Quita cualquier rastro de la clave de API de un texto antes de mostrarlo.

    Los mensajes de error de las librerias a veces incluyen la cabecera de
    autorizacion. El repositorio es publico y estos mensajes pueden terminar en una
    captura de pantalla del informe o del video, asi que se filtran siempre, aunque
    la libreria hoy no los incluya: es una defensa que no cuesta nada mantener.
    """
    if TOGETHER_API_KEY and TOGETHER_API_KEY in texto:
        texto = texto.replace(TOGETHER_API_KEY, "***")
    return texto


def _crear_cliente() -> openai.OpenAI:
    return openai.OpenAI(
        api_key=TOGETHER_API_KEY,
        base_url=TOGETHER_BASE_URL,
        timeout=TIMEOUT_SEGUNDOS,
    )


def transcribir(audio_wav: io.BytesIO, cliente: openai.OpenAI | None = None) -> str:
    """Convierte el WAV en texto. Devuelve cadena vacia si no se escucho nada.

    `cliente` se puede inyectar para las pruebas; en la aplicacion se deja en None y
    se construye uno nuevo con la configuracion del proyecto.
    """
    cliente = cliente or _crear_cliente()

    # Rebobinar es obligatorio: si alguien ya leyo el bufer, el puntero quedo al
    # final y se subiria un archivo de cero bytes sin que nada avise.
    audio_wav.seek(0)

    try:
        respuesta = cliente.audio.transcriptions.create(
            model=MODELO_STT,
            file=audio_wav,
            language=IDIOMA_STT,
        )
    except openai.APITimeoutError as excepcion:
        # Mismo criterio que en llm_engine: un tiempo de espera agotado no es lo mismo
        # que no tener red, y decirle a la usuaria que revise el wifi cuando el wifi
        # funciona la manda a arreglar algo que no esta roto.
        raise SinConexionSTT(
            "La transcripcion esta tardando demasiado. Puede que la conexion este "
            "lenta; intentalo otra vez con una frase mas corta."
        ) from excepcion
    except openai.APIConnectionError as excepcion:
        raise SinConexionSTT(
            "No se pudo enviar el audio para transcribir. Revisa tu conexion a "
            "internet e intenta de nuevo."
        ) from excepcion
    except (openai.AuthenticationError, openai.PermissionDeniedError) as excepcion:
        raise CredencialRechazadaSTT(
            "El servicio rechazo las credenciales. Verifica que TOGETHER_API_KEY en "
            "el archivo .env sea correcta y que la cuenta tenga saldo disponible."
        ) from excepcion
    except openai.RateLimitError as excepcion:
        # En Together AI, quedarse sin saldo llega como 429, igual que exceder el
        # ritmo de peticiones. Se agrupan porque la accion de la usuaria es la misma:
        # esperar o recargar.
        raise CredencialRechazadaSTT(
            "El servicio esta limitando las peticiones o la cuenta se quedo sin "
            "saldo. Espera un momento y vuelve a intentar."
        ) from excepcion
    except openai.APIStatusError as excepcion:
        raise TranscripcionFallida(
            "El servicio de transcripcion respondio con un error "
            f"(codigo {excepcion.status_code}). Intenta de nuevo en un momento."
        ) from excepcion
    except Exception as excepcion:  # noqa: BLE001 - red a nivel de sistema operativo
        raise TranscripcionFallida(
            "Ocurrio un problema inesperado al transcribir el audio: "
            + _sin_credenciales(str(excepcion))
        ) from excepcion

    return _texto_de(respuesta)


def _texto_de(respuesta) -> str:
    """Extrae el texto de la respuesta, tolerando las dos formas que puede llegar.

    La API devuelve normalmente un objeto con atributo `.text`, pero segun el formato
    pedido puede llegar como diccionario. Se aceptan ambos en vez de dar por sentado
    uno solo: es una linea de codigo que evita un fallo en plena demostracion.
    """
    if respuesta is None:
        return ""
    texto = getattr(respuesta, "text", None)
    if texto is None and isinstance(respuesta, dict):
        texto = respuesta.get("text")
    if texto is None:
        raise TranscripcionFallida(
            "El servicio devolvio una respuesta sin texto transcrito."
        )
    return texto.strip()
