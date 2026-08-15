"""Sintesis y reproduccion de voz (tarea T-08).

Convierte el texto de la respuesta en voz hablada y la reproduce por los altavoces.

QUE ES `edge-tts`: un cliente del servicio de sintesis de voz que usa el navegador
Microsoft Edge para su funcion de lectura en voz alta. No necesita clave de API ni
cuenta, y devuelve voces neuronales de calidad alta. Se eligio por eso: es la unica
pieza del pipeline que no consume saldo de Together AI.

POR QUE `asyncio.run()` AQUI DENTRO Y NO UN BUCLE PERMANENTE: `edge-tts` solo ofrece
API asincrona, pero el resto de Mini-JARVIS es sincrono a proposito (seccion 5 del
diseno: Tkinter obliga a que su mainloop viva en el hilo principal, y sostener un
bucle asyncio en paralelo es donde se pierden dias depurando ventanas congeladas).
La solucion es encapsular: `asyncio.run()` crea un bucle de eventos, lo usa para esta
sola llamada y lo destruye al terminar. El bucle nace y muere aqui dentro; hacia
afuera, `sintetizar()` es una funcion sincrona corriente.

DONDE CORRE ESTO: siempre en el hilo trabajador del turno, nunca en el hilo de la
GUI. `reproducir()` es BLOQUEANTE: no devuelve el control hasta que termina de sonar.
Eso es intencional — el orquestador necesita saber cuando la respuesta termino para
volver al estado de reposo — pero significa que llamarlo desde el hilo principal
congelaria la ventana.

FORMATO: el servicio devuelve MP3. Windows sabe reproducirlo sin ninguna libreria
extra a traves de MCI (Media Control Interface), la misma interfaz multimedia clasica
del sistema, a la que se llega con `ctypes`. Se evita asi anadir una dependencia mas
solo para reproducir un sonido.
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import tempfile
import uuid

import edge_tts

from config import VOZ_TTS


# --- Errores tipados --------------------------------------------------------

class ErrorDeTTS(RuntimeError):
    """Base de los fallos de voz. La GUI atrapa esta y muestra la respuesta escrita.

    Regla de la seccion 13 del diseno: si la voz falla, el turno NO se pierde. El
    texto de la respuesta ya esta en pantalla; que no suene es una degradacion, no
    un error fatal.
    """


class SintesisFallida(ErrorDeTTS):
    """El servicio de voz no devolvio audio (sin red, o texto vacio/rechazado)."""


class ReproduccionFallida(ErrorDeTTS):
    """Habia audio, pero el sistema no pudo reproducirlo."""


# El servicio rechaza el texto vacio y devolveria un audio de cero bytes.
_LONGITUD_MINIMA_TEXTO = 1


def sintetizar(texto: str, voz: str = VOZ_TTS) -> bytes:
    """Convierte texto en un MP3 en memoria. Sincrona por fuera, asincrona por dentro."""
    if texto is None or len(texto.strip()) < _LONGITUD_MINIMA_TEXTO:
        raise SintesisFallida(
            "No hay texto que leer en voz alta: la respuesta llego vacia."
        )

    try:
        audio = asyncio.run(_sintetizar_async(texto, voz))
    except ErrorDeTTS:
        raise
    except Exception as excepcion:  # noqa: BLE001 - fallo de red, DNS o del servicio
        raise SintesisFallida(
            "No se pudo generar la voz. El servicio de sintesis de Microsoft "
            "necesita conexion a internet; revisa la red e intenta de nuevo."
        ) from excepcion

    if not audio:
        raise SintesisFallida(
            "El servicio de sintesis devolvio un audio vacio para este texto."
        )
    return audio


async def _sintetizar_async(texto: str, voz: str) -> bytes:
    """Acumula los fragmentos de audio que el servicio va enviando por streaming.

    `edge-tts` entrega el audio a pedazos segun lo va generando, intercalados con
    metadatos de sincronizacion de palabras (WordBoundary) que a nosotros no nos
    sirven: solo se conservan los fragmentos de tipo "audio".
    """
    comunicacion = edge_tts.Communicate(texto, voz)
    fragmentos = bytearray()
    async for fragmento in comunicacion.stream():
        if fragmento["type"] == "audio":
            fragmentos.extend(fragmento["data"])
    return bytes(fragmentos)


def reproducir(audio_mp3: bytes) -> None:
    """Reproduce el MP3 y no devuelve el control hasta que termina de sonar.

    MCI trabaja sobre archivos, no sobre memoria, asi que el audio se escribe en un
    archivo temporal del sistema y se borra siempre al terminar (bloque `finally`),
    incluso si la reproduccion falla a la mitad. A diferencia del audio del
    microfono, esto no es un dato personal: es la respuesta sintetizada del propio
    asistente.
    """
    if not audio_mp3:
        raise ReproduccionFallida("No hay audio que reproducir.")

    # Nombre unico: si dos turnos se solaparan, no deben pisarse el archivo.
    ruta = os.path.join(tempfile.gettempdir(), f"minijarvis-{uuid.uuid4().hex}.mp3")
    with open(ruta, "wb") as archivo:
        archivo.write(audio_mp3)

    # Alias propio por reproduccion, por la misma razon que el nombre unico.
    alias = f"minijarvis{uuid.uuid4().hex[:8]}"
    try:
        # "type mpegvideo" es el driver de MCI que entiende MP3 en Windows.
        _mci(f'open "{ruta}" type mpegvideo alias {alias}')
        try:
            # "wait" es lo que hace bloqueante la llamada: MCI no regresa hasta que
            # el audio termino de sonar.
            _mci(f"play {alias} wait")
        finally:
            _mci(f"close {alias}", tolerar_error=True)
    finally:
        try:
            os.remove(ruta)
        except OSError:
            # Que no se pueda borrar un temporal no justifica romper el turno.
            pass


def _mci(comando: str, tolerar_error: bool = False) -> None:
    """Envia un comando a MCI y traduce su codigo de error a una excepcion nuestra."""
    try:
        codigo = ctypes.windll.winmm.mciSendStringW(comando, None, 0, None)
    except AttributeError as excepcion:  # no es Windows
        raise ReproduccionFallida(
            "La reproduccion de voz de Mini-JARVIS usa la interfaz multimedia de "
            "Windows y este sistema no la tiene."
        ) from excepcion

    if codigo != 0 and not tolerar_error:
        raise ReproduccionFallida(
            "El sistema no pudo reproducir la respuesta hablada. Revisa que haya "
            "un dispositivo de salida de audio activo y que el volumen no este en "
            f"silencio. (codigo MCI {codigo})"
        )


def hablar(texto: str, voz: str = VOZ_TTS) -> None:
    """Sintetiza y reproduce en una sola llamada. Es lo que usa el orquestador (T-09).

    Bloquea hasta que termina de sonar. Cualquier fallo sale como ErrorDeTTS, nunca
    como una excepcion cruda de red o de ctypes.
    """
    reproducir(sintetizar(texto, voz))


if __name__ == "__main__":
    # Comprobacion manual del check humano H-07:
    #     python -m core.tts_engine
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    frase = (
        "Hola, soy Mini-JARVIS. Soy una inteligencia artificial, asi que mis "
        "respuestas pueden contener errores."
    )
    print(f"Voz: {VOZ_TTS}")
    audio = sintetizar(frase)
    print(f"MP3 sintetizado: {len(audio)} bytes.")
    print("Reproduciendo... (la llamada no regresa hasta que termine de sonar)")
    reproducir(audio)
    print("Listo: el control volvio al terminar el audio.")
