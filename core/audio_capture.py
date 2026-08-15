"""Captura de audio del microfono (tarea T-05).

Convierte lo que entra por el microfono en bytes WAV que viven UNICAMENTE en memoria.

POR QUE EN MEMORIA Y NO EN UN ARCHIVO TEMPORAL: la voz de la usuaria es un dato
personal. Escribirla en disco crea una copia que hay que acordarse de borrar, que
puede quedar huerfana si la aplicacion se cierra a mitad de un turno, y que en
Windows puede quedar bloqueada por otro proceso. Un `io.BytesIO` desaparece solo
cuando nadie lo referencia. Ademas es mas rapido: el cliente de transcripcion sube
el mismo objeto sin pasar por el sistema de archivos.

POR QUE PUSH-TO-TALK Y NO UN TEMPORIZADOR: la grabacion empieza y termina cuando la
usuaria lo decide (manteniendo el boton o la barra espaciadora). Un temporizador fijo
cortaria frases largas por la mitad y grabaria silencio en las cortas. Por eso esta
clase expone `iniciar()` y `detener()` como dos llamadas separadas y no tiene ninguna
nocion de duracion maxima propia.

FORMATO DE SALIDA: WAV PCM de 16 bits, mono, a 16 kHz. Es el formato que esperan los
modelos de la familia Whisper (internamente remuestrean a 16 kHz de todos modos, asi
que grabar a mas no anade informacion util y solo hace el archivo mas pesado de
subir). Mono porque un microfono de laptop no aporta nada en estereo.

Este modulo no habla con ninguna API ni con la GUI: solo produce bytes. Los errores
salen como excepciones tipadas de este modulo para que la GUI pueda mostrar un
mensaje amable en lugar de una traza tecnica (seccion 13 del diseno).
"""

from __future__ import annotations

import io
import wave

import numpy as np
import sounddevice as sd


# --- Errores tipados --------------------------------------------------------

class ErrorDeAudio(RuntimeError):
    """Base de todos los fallos de captura. La GUI puede atrapar solo esta."""


class MicrofonoNoDisponible(ErrorDeAudio):
    """No hay dispositivo de entrada, o el sistema no da permiso para usarlo."""


class GrabacionInvalida(ErrorDeAudio):
    """Se pidio una operacion en un orden imposible (detener sin haber iniciado)."""


class GrabacionVacia(ErrorDeAudio):
    """La grabacion termino sin un solo bloque de audio: no hay nada que transcribir."""


# --- Parametros de captura --------------------------------------------------

FRECUENCIA_MUESTREO = 16_000  # Hz. El nativo de Whisper.
CANALES = 1                   # mono
ANCHO_MUESTRA_BYTES = 2       # 16 bits por muestra (formato "int16")
NOMBRE_ARCHIVO_LOGICO = "grabacion.wav"


def verificar_microfono(dispositivo=None) -> str:
    """Comprueba que exista un microfono utilizable y devuelve su nombre.

    Se llama al arrancar la aplicacion para fallar temprano y con un mensaje claro,
    en vez de descubrirlo la primera vez que la usuaria intenta hablar.
    """
    try:
        info = sd.query_devices(dispositivo, kind="input")
    except Exception as excepcion:  # noqa: BLE001 - PortAudio agrupa varios fallos aqui
        raise MicrofonoNoDisponible(
            "No se encontro ningun microfono disponible. Revisa que haya un "
            "microfono conectado y que Windows le haya dado permiso a esta "
            "aplicacion en Configuracion > Privacidad > Microfono."
        ) from excepcion

    if info.get("max_input_channels", 0) < 1:
        raise MicrofonoNoDisponible(
            f"El dispositivo '{info.get('name', 'desconocido')}' no tiene canales de "
            "entrada, asi que no puede grabar. Elige otro dispositivo de entrada."
        )
    return info.get("name", "desconocido")


class GrabadoraDeVoz:
    """Graba del microfono entre `iniciar()` y `detener()`, en memoria.

    Uso previsto desde la GUI (push-to-talk):

        grabadora = GrabadoraDeVoz()
        grabadora.iniciar()     # al presionar el boton
        ...                     # la usuaria habla
        audio = grabadora.detener()   # al soltar -> io.BytesIO con un WAV dentro
    """

    def __init__(self, dispositivo=None,
                 frecuencia: int = FRECUENCIA_MUESTREO,
                 canales: int = CANALES) -> None:
        self.dispositivo = dispositivo
        self.frecuencia = frecuencia
        self.canales = canales
        self._stream: sd.InputStream | None = None
        # PortAudio entrega el audio en bloques pequenos desde su propio hilo; se van
        # acumulando aqui y solo al final se pegan en un unico WAV.
        self._bloques: list[np.ndarray] = []

    @property
    def esta_grabando(self) -> bool:
        return self._stream is not None

    def _al_recibir_audio(self, datos, marcos, tiempo, estado) -> None:
        """Callback de PortAudio. Corre en un hilo propio de la libreria.

        Regla de oro: aqui no se hace nada lento ni nada que pueda fallar. Si este
        callback se demora, PortAudio pierde muestras y el audio sale entrecortado.
        Por eso solo se copia el bloque a una lista; todo el trabajo real (armar el
        WAV) se hace despues, en detener().

        `datos` se COPIA a proposito: PortAudio reutiliza ese mismo bufer para el
        siguiente bloque, asi que guardarlo sin copiar terminaria con toda la
        grabacion apuntando al ultimo fragmento.
        """
        self._bloques.append(datos.copy())

    def iniciar(self) -> None:
        """Abre el microfono y empieza a acumular audio."""
        if self.esta_grabando:
            raise GrabacionInvalida(
                "Ya hay una grabacion en curso. Detenla antes de iniciar otra."
            )

        verificar_microfono(self.dispositivo)
        self._bloques = []

        try:
            self._stream = sd.InputStream(
                samplerate=self.frecuencia,
                channels=self.canales,
                dtype="int16",
                device=self.dispositivo,
                callback=self._al_recibir_audio,
            )
            self._stream.start()
        except Exception as excepcion:  # noqa: BLE001 - cualquier fallo de PortAudio
            self._stream = None
            raise MicrofonoNoDisponible(
                "No se pudo abrir el microfono para grabar. Puede que otra "
                "aplicacion lo tenga ocupado (una videollamada, por ejemplo). "
                "Cierrala e intenta de nuevo."
            ) from excepcion

    def detener(self) -> io.BytesIO:
        """Cierra el microfono y devuelve un WAV completo en memoria.

        El objeto devuelto lleva un atributo `.name`: el cliente de transcripcion
        (T-06) deduce de ahi que esta subiendo un `.wav`. Sin nombre, la API no sabe
        que formato le llego.
        """
        if not self.esta_grabando:
            raise GrabacionInvalida(
                "No hay ninguna grabacion en curso que detener."
            )

        stream, self._stream = self._stream, None
        try:
            stream.stop()
        finally:
            # Cerrar siempre, incluso si stop() falla: un stream sin cerrar deja el
            # microfono tomado hasta que se cierre la aplicacion entera.
            stream.close()

        if not self._bloques:
            raise GrabacionVacia(
                "No se capturo audio. Manten presionado el boton mientras hablas: "
                "si se suelta de inmediato no da tiempo a grabar nada."
            )

        audio = np.concatenate(self._bloques, axis=0)
        self._bloques = []
        return self._a_wav_en_memoria(audio)

    def cancelar(self) -> None:
        """Corta la grabacion y tira el audio. Para cuando la usuaria se arrepiente."""
        if self.esta_grabando:
            stream, self._stream = self._stream, None
            try:
                stream.stop()
            finally:
                stream.close()
        self._bloques = []

    def _a_wav_en_memoria(self, audio: np.ndarray) -> io.BytesIO:
        """Envuelve las muestras crudas en la cabecera de un archivo WAV.

        Las muestras por si solas son solo numeros: el WAV les antepone una cabecera
        que declara frecuencia, canales y tamano de muestra, que es lo que permite a
        quien reciba el archivo interpretarlos como sonido.
        """
        bufer = io.BytesIO()
        with wave.open(bufer, "wb") as archivo_wav:
            archivo_wav.setnchannels(self.canales)
            archivo_wav.setsampwidth(ANCHO_MUESTRA_BYTES)
            archivo_wav.setframerate(self.frecuencia)
            archivo_wav.writeframes(audio.tobytes())

        bufer.seek(0)  # se deja al inicio: quien lo reciba lo va a leer entero
        bufer.name = NOMBRE_ARCHIVO_LOGICO
        return bufer

    def duracion_segundos(self) -> float:
        """Segundos acumulados hasta ahora. La GUI puede mostrarlo mientras se graba."""
        marcos = sum(len(bloque) for bloque in self._bloques)
        return marcos / float(self.frecuencia)


if __name__ == "__main__":
    # Comprobacion manual del check humano H-04: graba unos segundos y reporta.
    # No forma parte de la aplicacion; se ejecuta con:
    #     python -m core.audio_capture
    import sys
    import time

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(f"Microfono detectado: {verificar_microfono()}")
    grabadora = GrabadoraDeVoz()
    print("Grabando 3 segundos... habla ahora.")
    grabadora.iniciar()
    time.sleep(3)
    audio = grabadora.detener()
    datos = audio.getvalue()
    print(f"WAV en memoria: {len(datos)} bytes, nombre logico '{audio.name}'.")
    print(f"Cabecera RIFF correcta: {datos[:4] == b'RIFF' and datos[8:12] == b'WAVE'}")
