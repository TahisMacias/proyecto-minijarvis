"""Pruebas del respaldo sin internet (T-21).

Aqui NO se carga ningun modelo local: cargarlos cuesta medio minuto y esta suite tiene
que seguir corriendo en cuatro segundos. Lo que se prueba es la LOGICA DE DECISION, que
es donde estan los errores posibles: cuando cambiar a local, cuando no, y que no se
pierda nada por el camino.

La regla que mas importa de todas es la ultima del archivo: un fallo de credenciales NO
debe activar el respaldo. Si la clave esta mal, cambiar al modelo pequeno esconderia el
problema real y la duena se pasaria la sustentacion preguntandose por que responde tan
mal.
"""

import pytest

from core.llm_engine import (
    CredencialRechazadaLLM,
    ModeloDemasiadoLento,
    RespuestaInvalida,
    SinConexionLLM,
)
from core.modo_local import (
    MotorConRespaldo,
    RespuestaLocal,
    TranscriptorConRespaldo,
    VozConRespaldo,
    _es_falta_de_red,
)
from core.stt_client import CredencialRechazadaSTT, SinConexionSTT
from core.tts_engine import SintesisFallida


# ===========================================================================
# Que cuenta como "no hay internet" y que no
# ===========================================================================

@pytest.mark.parametrize("excepcion", [
    SinConexionLLM("sin red"),
    SinConexionSTT("sin red"),
    SintesisFallida("sin red"),
    ModeloDemasiadoLento("tarda demasiado"),
])
def test_estas_si_activan_el_respaldo(excepcion):
    assert _es_falta_de_red(excepcion)


@pytest.mark.parametrize("excepcion", [
    CredencialRechazadaLLM("clave mala"),
    CredencialRechazadaSTT("clave mala"),
    RespuestaInvalida("el servidor devolvio basura"),
    ValueError("un error cualquiera del programa"),
])
def test_estas_NO_activan_el_respaldo(excepcion):
    """La regla mas importante del modulo.

    Si la clave de API esta mal o la cuenta se quedo sin saldo, caer al modelo local
    haria que la aplicacion pareciera funcionar -mal- en vez de decir lo que pasa. El
    respaldo es para la falta de red, no para tapar cualquier fallo.
    """
    assert not _es_falta_de_red(excepcion)


# ===========================================================================
# Dobles
# ===========================================================================

class MotorFalso:
    def __init__(self, excepcion=None):
        self.excepcion = excepcion
        self.llamadas = 0
        self.modelo = "modelo-de-la-nube"
        self.temperatura = 0.7
        self.top_p = 0.9

    def responder(self, mensajes, temperatura=None, top_p=None, herramientas=None):
        self.llamadas += 1
        if self.excepcion:
            raise self.excepcion
        return RespuestaLocal("respuesta de la nube")

    def cambiar_modelo(self, modelo):
        self.modelo = modelo


class MotorLocalFalso:
    def __init__(self):
        self.llamadas = 0
        self.temperatura = 0.7
        self.top_p = 0.9
        self.mensajes_recibidos = None

    def responder(self, mensajes, temperatura=None, top_p=None, herramientas=None):
        self.llamadas += 1
        self.mensajes_recibidos = list(mensajes)
        return RespuestaLocal("respuesta local")


# ===========================================================================
# El motor
# ===========================================================================

def test_con_internet_no_se_toca_el_modelo_local():
    nube, local = MotorFalso(), MotorLocalFalso()
    motor = MotorConRespaldo(nube, local)

    respuesta = motor.responder([{"role": "user", "content": "hola"}])

    assert respuesta.texto == "respuesta de la nube"
    assert local.llamadas == 0, "cargo el modelo local sin hacer falta"
    assert not motor.usando_local


def test_sin_internet_responde_el_local_y_lo_avisa():
    avisos = []
    nube = MotorFalso(SinConexionLLM("sin red"))
    local = MotorLocalFalso()
    motor = MotorConRespaldo(nube, local, avisar=avisos.append)

    respuesta = motor.responder([{"role": "user", "content": "hola"}])

    assert respuesta.texto == "respuesta local"
    assert motor.usando_local
    assert len(avisos) == 1, "no aviso del cambio de modo"
    assert "modelo local" in avisos[0]


def test_una_credencial_rechazada_NO_cae_al_local():
    """Debe propagarse tal cual, para que la GUI muestre el mensaje verdadero."""
    nube = MotorFalso(CredencialRechazadaLLM("clave invalida"))
    local = MotorLocalFalso()
    motor = MotorConRespaldo(nube, local)

    with pytest.raises(CredencialRechazadaLLM):
        motor.responder([{"role": "user", "content": "hola"}])
    assert local.llamadas == 0


def test_el_motor_reintenta_la_nube_en_cada_turno():
    """Es la pieza que mas se nota, asi que vale el segundo de comprobar si volvio."""
    nube = MotorFalso(SinConexionLLM("sin red"))
    motor = MotorConRespaldo(nube, MotorLocalFalso())

    motor.responder([{"role": "user", "content": "uno"}])
    motor.responder([{"role": "user", "content": "dos"}])

    assert nube.llamadas == 2, "dejo de intentar la nube"


def test_cuando_vuelve_la_conexion_lo_dice_y_deja_de_usar_el_local():
    avisos = []
    nube = MotorFalso(SinConexionLLM("sin red"))
    motor = MotorConRespaldo(nube, MotorLocalFalso(), avisar=avisos.append)

    motor.responder([{"role": "user", "content": "sin red"}])
    assert motor.usando_local

    nube.excepcion = None
    respuesta = motor.responder([{"role": "user", "content": "ya hay red"}])

    assert respuesta.texto == "respuesta de la nube"
    assert not motor.usando_local
    assert any("Volvio la conexion" in a for a in avisos)


def test_la_conversacion_sobrevive_al_cambio_de_modo():
    """Lo que hay que proteger: el hilo de la charla, no el modelo que la atiende."""
    local = MotorLocalFalso()
    motor = MotorConRespaldo(MotorFalso(SinConexionLLM("x")), local)

    historial = [
        {"role": "system", "content": "prompt largo de la nube"},
        {"role": "user", "content": "mi color favorito es el verde"},
        {"role": "assistant", "content": "que bonito"},
        {"role": "user", "content": "cual dije que era?"},
    ]
    motor.responder(historial)

    recibidos = local.mensajes_recibidos
    assert any("verde" in str(m.get("content")) for m in recibidos), (
        "se perdio la conversacion al cambiar de modelo"
    )


def test_el_selector_de_modelo_sigue_actuando_sobre_la_nube():
    nube = MotorFalso()
    motor = MotorConRespaldo(nube, MotorLocalFalso())
    motor.cambiar_modelo("otro-modelo")
    assert nube.modelo == "otro-modelo"
    assert motor.modelo == "otro-modelo"


def test_los_sliders_llegan_a_las_dos_piezas():
    nube, local = MotorFalso(SinConexionLLM("x")), MotorLocalFalso()
    motor = MotorConRespaldo(nube, local)
    motor.temperatura = 1.2
    motor.top_p = 0.5

    motor.responder([{"role": "user", "content": "hola"}])

    assert nube.temperatura == 1.2, "el slider no llego a la nube"
    assert local.temperatura == 1.2, "el slider no llego al modelo local"


# ===========================================================================
# Oido y voz
# ===========================================================================

def test_el_oido_cae_al_local_solo_si_falta_la_red():
    llamadas = []

    def nube_rota(_audio):
        raise SinConexionSTT("sin red")

    def local(_audio):
        llamadas.append("local")
        return "lo que dijo"

    oido = TranscriptorConRespaldo(nube_rota, local)
    assert oido(b"audio") == "lo que dijo"
    assert llamadas == ["local"]


def test_el_oido_no_cae_al_local_por_una_credencial_mala():
    def nube_rota(_audio):
        raise CredencialRechazadaSTT("clave mala")

    def local(_audio):
        raise AssertionError("no debio llamarse al local")

    with pytest.raises(CredencialRechazadaSTT):
        TranscriptorConRespaldo(nube_rota, local)(b"audio")


def test_la_voz_cae_a_la_de_windows_sin_red():
    dichos = []

    def nube_rota(_texto):
        raise SintesisFallida("sin red")

    voz = VozConRespaldo(nube_rota, dichos.append)
    voz("hola")
    assert dichos == ["hola"]


def test_la_respuesta_local_nunca_pide_herramientas():
    """Un modelo de 494M no elige bien entre cinco herramientas; mejor ninguna."""
    respuesta = RespuestaLocal("texto")
    assert respuesta.pide_herramienta is False
    assert respuesta.peticiones_de_tool == []
    assert respuesta.mensaje_crudo["role"] == "assistant"
