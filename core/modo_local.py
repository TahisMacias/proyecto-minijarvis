"""Modo sin internet: oir, pensar y hablar con modelos que viven en esta maquina.

POR QUE EXISTE ESTE ARCHIVO. El enunciado permite modelo por API **o** local, y hasta
el 2026-08-23 el proyecto solo hacia lo primero: sin conexion avisaba con elegancia y
se quedaba quieto. La duena apago el wifi cuatro veces y cuatro veces dijo que asi no
le servia. Es su proyecto: se hace.

QUE CAMBIA Y QUE NO. La nube sigue siendo el camino principal, porque es mucho mejor.
Lo local es un RESPALDO que entra solo cuando el camino principal falla por falta de
red. No hay que elegir nada ni tocar ningun ajuste: la aplicacion lo nota y cambia.

LO QUE CUESTA, MEDIDO EN ESTA MAQUINA Y DICHO DE FRENTE:

    pieza            en la nube        en local
    -----            ----------        --------
    oir              ~2 s              ~2 s (mas 18 s la primera vez, al cargar)
    pensar           1-3 s             ~4 palabras por segundo, y responde peor
    hablar           voz neuronal      voz de Windows, mas robotica

El modelo local tiene 494 millones de parametros; el de la nube, billones. La
diferencia se nota y no se disimula: cuando el respaldo entra, la aplicacion lo dice.

TODO SE CARGA CON PEREZA. Ninguno de los tres modelos se toca al arrancar: cargarlos
cuesta casi un minuto y la inmensa mayoria de las veces no hacen falta. Se cargan la
primera vez que se necesitan de verdad, y se quedan en memoria a partir de ahi.
"""

from __future__ import annotations

import io
import os
import tempfile
import threading

# Modelo pequeno a proposito: en una laptop sin tarjeta grafica, cualquier cosa mas
# grande tarda tanto que deja de ser un respaldo y pasa a ser una espera.
MODELO_LLM_LOCAL = "Qwen/Qwen2.5-0.5B-Instruct"

# "base" es el equilibrio: "tiny" se come palabras y "small" tarda el triple. Con el
# acento de la duena, base transcribe bien los numeros, que es la parte dificil.
MODELO_STT_LOCAL = "base"

# Un candado por modelo: la carga puede tardar medio minuto y dos turnos seguidos no
# deben empezar a cargar lo mismo dos veces.
_candado = threading.Lock()
_cargados: dict[str, object] = {}


class ModoLocalNoDisponible(RuntimeError):
    """Falta alguna libreria o algun modelo del respaldo local."""


# ===========================================================================
# Oir sin internet
# ===========================================================================

def _modelo_stt():
    with _candado:
        if "stt" not in _cargados:
            try:
                from faster_whisper import WhisperModel
            except ImportError as excepcion:
                raise ModoLocalNoDisponible(
                    "Para funcionar sin internet hace falta la libreria "
                    "faster-whisper. Instalala con: pip install -r requirements.txt"
                ) from excepcion
            # int8: cuantizado a enteros de 8 bits. Ocupa cuatro veces menos memoria y
            # va mas rapido en un procesador normal, a cambio de una perdida de
            # precision que en voz no se nota.
            _cargados["stt"] = WhisperModel(
                MODELO_STT_LOCAL, device="cpu", compute_type="int8"
            )
        return _cargados["stt"]


def transcribir_local(audio_wav: io.BytesIO) -> str:
    """Convierte el WAV en texto sin salir a internet.

    Recibe el mismo `io.BytesIO` que produce `core/audio_capture.py`, para que sea
    intercambiable con `core/stt_client.transcribir` sin que nadie mas se entere.
    """
    audio_wav.seek(0)
    modelo = _modelo_stt()

    # faster-whisper acepta un objeto con `read`, asi que no hace falta pasar por
    # disco: la voz de la usuaria sigue sin escribirse nunca en un archivo.
    segmentos, _info = modelo.transcribe(audio_wav, language="es")
    return " ".join(s.text for s in segmentos).strip()


# ===========================================================================
# Pensar sin internet
# ===========================================================================

def _modelo_llm():
    with _candado:
        if "llm" not in _cargados:
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer
            except ImportError as excepcion:
                raise ModoLocalNoDisponible(
                    "Para funcionar sin internet hacen falta torch y transformers."
                ) from excepcion
            tokenizador = AutoTokenizer.from_pretrained(MODELO_LLM_LOCAL)
            modelo = AutoModelForCausalLM.from_pretrained(
                MODELO_LLM_LOCAL, dtype=torch.float32
            )
            modelo.eval()
            _cargados["llm"] = (tokenizador, modelo, torch)
        return _cargados["llm"]


class RespuestaLocal:
    """Imita lo justo de `RespuestaDelModelo` para que el orquestador no note nada.

    El modelo local NO usa herramientas: 494 millones de parametros no eligen bien
    entre cinco herramientas, y una llamada mal elegida seria peor que ninguna. Por eso
    `pide_herramienta` es siempre False y el orquestador sigue de largo.
    """

    def __init__(self, texto: str) -> None:
        self.texto = texto
        self.peticiones_de_tool: list = []
        self.mensaje_crudo = {"role": "assistant", "content": texto}
        self.tools_descartadas: list = []

    @property
    def pide_herramienta(self) -> bool:
        return False


class MotorLocal:
    """Genera texto con el modelo pequeno de esta maquina.

    Expone `responder(mensajes, ...)` con la misma forma que `core/llm_engine.MotorLLM`
    para poder sustituirlo sin tocar el orquestador.
    """

    # Corto a proposito: a unas cuatro palabras por segundo, 80 tokens ya son veinte
    # segundos de espera. Mas largo no seria mejor respuesta, seria mas espera.
    MAXIMO_TOKENS = 80

    # EL MODELO LOCAL NECESITA SU PROPIO SYSTEM PROMPT, mas corto que el de la nube.
    #
    # Se probaron los dos con el mismo modelo. Con el prompt de la nube -697 caracteres,
    # con reglas de formato y mencion a las herramientas- el modelo se llamaba a si
    # mismo "Mini-JRASDOS" y contestaba "lo siento, no puedo asistir con eso" a
    # preguntas normales. Con este, cero negativas en tres preguntas seguidas y la
    # capital de Ecuador correcta.
    #
    # El detalle que mas costo encontrar: la frase "y puedes equivocarte", que en la
    # nube es una salvaguarda etica util, aqui el modelo la lee como una ORDEN y empieza
    # a negarse a responder ("no puedo, porque me equivoque"). Un modelo de 494 millones
    # de parametros no distingue una advertencia de una instruccion. Se quita de aqui.
    #
    # La seccion 11 del enunciado sigue cumplida por otras dos vias que no dependen de
    # este modelo: el primer mensaje de la ventana lo dice al abrirse, y el indicador de
    # modo avisa de que esta respondiendo el modelo pequeno.
    SYSTEM_PROMPT_LOCAL = (
        "Eres Mini-JARVIS, un asistente de voz en espanol. Eres una inteligencia "
        "artificial. Responde siempre, en una o dos frases cortas y en espanol."
    )

    def __init__(self) -> None:
        self.modelo = MODELO_LLM_LOCAL
        self.temperatura = 0.7
        self.top_p = 0.9

    def cambiar_modelo(self, modelo: str) -> None:
        """El respaldo tiene un solo modelo. Se acepta la llamada y no se hace nada."""

    def responder(self, mensajes, temperatura=None, top_p=None, herramientas=None):
        tokenizador, modelo, torch = _modelo_llm()

        # Se sustituye el system prompt de la nube por el corto. La conversacion -lo
        # que dijo la usuaria y lo que se respondio- se conserva intacta: el hilo de la
        # charla no se pierde al caerse la red, que es justo lo que hay que proteger.
        conversacion = [m for m in mensajes if m.get("role") != "system"]
        mensajes_locales = [
            {"role": "system", "content": self.SYSTEM_PROMPT_LOCAL}
        ] + conversacion

        # El manifiesto de herramientas se descarta: ver RespuestaLocal.
        texto = tokenizador.apply_chat_template(
            mensajes_locales, tokenize=False, add_generation_prompt=True
        )
        entradas = tokenizador(texto, return_tensors="pt")

        with torch.no_grad():
            salida = modelo.generate(
                **entradas,
                max_new_tokens=self.MAXIMO_TOKENS,
                do_sample=True,
                temperature=self.temperatura if temperatura is None else temperatura,
                top_p=self.top_p if top_p is None else top_p,
                pad_token_id=tokenizador.eos_token_id,
            )

        nuevos = salida[0][entradas["input_ids"].shape[1]:]
        return RespuestaLocal(
            tokenizador.decode(nuevos, skip_special_tokens=True).strip()
        )


# ===========================================================================
# Hablar sin internet
# ===========================================================================

def hablar_local(texto: str) -> None:
    """Lee el texto con una voz instalada en Windows. Bloquea hasta terminar.

    POR QUE UN PROCESO NUEVO CADA VEZ, y no un motor reutilizado: `pyttsx3` se apoya en
    SAPI a traves de COM, y COM se lleva mal con que un objeto creado en un hilo se use
    desde otro. Aqui cada turno corre en un hilo trabajador distinto, asi que reutilizar
    el motor produce cuelgues intermitentes -de los que aparecen una vez de cada veinte
    y justo el dia de la sustentacion. Crear y destruir el motor en cada llamada cuesta
    unas decimas y elimina esa clase entera de fallo.
    """
    if not texto or not texto.strip():
        return

    try:
        import pyttsx3
    except ImportError as excepcion:
        raise ModoLocalNoDisponible(
            "Para hablar sin internet hace falta la libreria pyttsx3."
        ) from excepcion

    motor = pyttsx3.init()
    try:
        for voz in motor.getProperty("voices"):
            if "ES-ES" in voz.id.upper() or "SPANISH" in voz.id.upper():
                motor.setProperty("voice", voz.id)
                break
        motor.say(texto)
        motor.runAndWait()
    finally:
        try:
            motor.stop()
        except Exception:  # noqa: BLE001 - cerrar el motor nunca debe romper el turno
            pass


# ===========================================================================
# Los envoltorios: nube primero, local si no hay red
# ===========================================================================
#
# Cada uno tiene la misma forma que la pieza de nube a la que sustituye, asi que el
# orquestador los recibe sin enterarse de que existen. Esa es la razon de que este
# archivo no obligue a tocar ni una linea de core/orchestrator.py.


def _es_falta_de_red(excepcion: BaseException) -> bool:
    """True si la excepcion significa "no hay internet" y no otra cosa.

    Se mira el NOMBRE de la clase y no se importan los tipos, para que este modulo no
    dependa de los otros y siga siendo el ultimo eslabon. Y se distingue de un fallo de
    credenciales a proposito: si la clave es invalida, cambiar al modelo local
    esconderia el problema real en vez de resolverlo.
    """
    nombre = type(excepcion).__name__
    return nombre in ("SinConexionLLM", "SinConexionSTT", "SintesisFallida",
                      "ModeloDemasiadoLento")


class ConRespaldo:
    """Envuelve una pieza de nube y su equivalente local.

    Guarda si el respaldo esta activo para que la interfaz pueda decirlo: un asistente
    que de pronto responde peor y no explica por que es peor que uno que falla.
    """

    def __init__(self, en_la_nube, en_local, avisar=None) -> None:
        self._nube = en_la_nube
        self._local = en_local
        self._avisar = avisar
        self.usando_local = False

    def _cambiar_a_local(self, motivo: str) -> None:
        if not self.usando_local:
            self.usando_local = True
            if self._avisar:
                self._avisar(motivo)

    def _volver_a_la_nube(self) -> None:
        if self.usando_local:
            self.usando_local = False
            if self._avisar:
                self._avisar("Volvio la conexion. Ya responde el modelo grande.")


class TranscriptorConRespaldo(ConRespaldo):
    def __call__(self, audio):
        if not self.usando_local:
            try:
                resultado = self._nube(audio)
                self._volver_a_la_nube()
                return resultado
            except Exception as excepcion:  # noqa: BLE001
                if not _es_falta_de_red(excepcion):
                    raise
                self._cambiar_a_local(
                    "Sin internet. Cambio al modo local: la primera vez tarda unos "
                    "segundos en arrancar."
                )
        # Ya en local. Se reintenta la nube de vez en cuando desde el motor, no aqui:
        # probar en cada transcripcion anadiria la espera del timeout a cada turno.
        return self._local(audio)


class MotorConRespaldo(ConRespaldo):
    """Motor que prueba la nube y cae al modelo local si no hay red.

    A diferencia del transcriptor, este SI reintenta la nube en cada turno: es la pieza
    que mas se nota, y volver al modelo grande en cuanto haya conexion vale el segundo
    que cuesta descubrir que sigue sin haberla.
    """

    def __init__(self, en_la_nube, en_local, avisar=None) -> None:
        super().__init__(en_la_nube, en_local, avisar)
        self.modelo = getattr(en_la_nube, "modelo", "")
        self.temperatura = getattr(en_la_nube, "temperatura", 0.7)
        self.top_p = getattr(en_la_nube, "top_p", 0.9)

    def cambiar_modelo(self, modelo: str) -> None:
        self._nube.cambiar_modelo(modelo)
        self.modelo = modelo

    def responder(self, mensajes, temperatura=None, top_p=None, herramientas=None):
        self._nube.temperatura = self.temperatura
        self._nube.top_p = self.top_p
        try:
            respuesta = self._nube.responder(
                mensajes, temperatura, top_p, herramientas
            )
            self._volver_a_la_nube()
            return respuesta
        except Exception as excepcion:  # noqa: BLE001
            if not _es_falta_de_red(excepcion):
                raise
            self._cambiar_a_local(
                "Sin internet. Responde el modelo local, que es mucho mas pequeno: "
                "sus respuestas son mas cortas y menos acertadas, y no usa herramientas."
            )

        self._local.temperatura = self.temperatura
        self._local.top_p = self.top_p
        return self._local.responder(mensajes, temperatura, top_p, None)


class VozConRespaldo(ConRespaldo):
    def __call__(self, texto):
        if not self.usando_local:
            try:
                self._nube(texto)
                return
            except Exception as excepcion:  # noqa: BLE001
                if not _es_falta_de_red(excepcion):
                    raise
                self._cambiar_a_local("Sin internet. Hablo con la voz de Windows.")
        self._local(texto)


def precalentar_en_segundo_plano(avisar=None) -> threading.Thread:
    """Carga los modelos locales en un hilo aparte, nada mas arrancar la aplicacion.

    POR QUE ESTO EXISTE. Sin precalentar, el primer turno sin internet tardaba mas de
    un minuto: 18 s en cargar Whisper, 37 s en cargar el modelo de lenguaje y otros
    veinte en generar. La duena apago el wifi, vio "Pensando..." durante todo ese rato
    y dio por hecho que no funcionaba. Tenia razon en darlo por hecho: **un minuto sin
    ninguna senal es indistinguible de estar colgado.**

    Cargarlos por adelantado mueve esa espera al arranque, donde nadie la nota porque
    la aplicacion ya esta usable mientras tanto. Cuesta memoria -unos 2 GB- y ese es el
    precio de que el cambio a local sea instantaneo cuando de verdad hace falta.

    Es un hilo `daemon`: si se cierra la ventana a mitad de la carga, no deja el
    proceso colgado esperandolo.

    Si los modelos no estan descargados todavia, esto falla en silencio y no pasa nada:
    el respaldo seguira funcionando, solo que cargando en el momento. El aviso de que
    hay que descargarlos vive en el README y en `descargar_modelos_locales`.
    """
    def preparar():
        try:
            _modelo_stt()
            _modelo_llm()
        except Exception:  # noqa: BLE001 - precalentar nunca debe romper el arranque
            return
        if avisar:
            avisar("listo")

    hilo = threading.Thread(target=preparar, name="minijarvis-precalentar",
                            daemon=True)
    hilo.start()
    return hilo


def modelos_locales_listos() -> bool:
    """True si los dos modelos ya estan en memoria y el cambio seria instantaneo."""
    return "stt" in _cargados and "llm" in _cargados


def descargar_modelos_locales(informar=print) -> None:
    """Baja y calienta los tres modelos locales. Se ejecuta a mano, no al arrancar.

        python -m core.modo_local

    Conviene correrlo UNA vez con internet antes de la sustentacion: si no, la primera
    vez que se caiga la red habra que descargar cientos de megas justo entonces, que es
    el peor momento posible.
    """
    import time

    informar("Preparando el modo sin internet. Solo hay que hacerlo una vez.\n")

    t0 = time.time()
    informar("1/3  Descargando el modelo de voz a texto...")
    _modelo_stt()
    informar(f"     listo en {time.time() - t0:.0f} s")

    t0 = time.time()
    informar("2/3  Descargando el modelo de lenguaje local...")
    _modelo_llm()
    informar(f"     listo en {time.time() - t0:.0f} s")

    informar("3/3  Comprobando la voz de Windows...")
    hablar_local("Modo sin internet listo.")
    informar("     listo")

    informar("\nYa puedes apagar el wifi: la aplicacion seguira funcionando.")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    descargar_modelos_locales()
