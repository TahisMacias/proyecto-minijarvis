"""Pruebas del orquestador y su maquina de estados (tarea T-09).

Todo corre con dobles: ni microfono, ni red, ni saldo. Lo que se verifica es la
coreografia del turno, que es donde vive el riesgo de esta tarea.

Las invariantes que se prueban aqui son las que, si se rompen, arruinan la
sustentacion en vivo:

  - de ATENCION SIEMPRE se vuelve a REPOSO (la aplicacion nunca se queda trabada);
  - ninguna excepcion escapa del hilo trabajador;
  - el turno usa un hilo efimero, que termina;
  - el maximo de rondas de tool calling se respeta;
  - un fallo de voz no borra la respuesta ya mostrada.

Los dobles son clases pequenas escritas a mano en vez de `unittest.mock`: se lee de
un vistazo que hace cada una, que importa mas que la brevedad cuando estas pruebas
hay que explicarlas en una sustentacion oral.
"""

import io

import pytest

from core.llm_engine import PeticionDeTool, RespuestaDelModelo
from core.memory import MemoriaConversacional
from core.orchestrator import Estado, Evento, Orquestador, TipoEvento


ESPERA_MAXIMA = 5  # segundos; si un turno tarda mas que esto, algo se colgo


# --- Dobles ----------------------------------------------------------------

class ErrorDePruebaDelProyecto(RuntimeError):
    """Imita un error tipado de core/: su texto ya esta redactado para la usuaria."""


# El orquestador reconoce los errores "presentables" por el modulo donde se define la
# clase. Se falsea aqui para no tener que importar los errores de los cinco modulos.
ErrorDePruebaDelProyecto.__module__ = "core.falso"


class GrabadoraFalsa:
    def __init__(self, fallo_al_iniciar=None, fallo_al_detener=None):
        self.fallo_al_iniciar = fallo_al_iniciar
        self.fallo_al_detener = fallo_al_detener
        self.iniciada = False
        self.cancelada = False

    def iniciar(self):
        if self.fallo_al_iniciar:
            raise self.fallo_al_iniciar
        self.iniciada = True

    def detener(self):
        if self.fallo_al_detener:
            raise self.fallo_al_detener
        self.iniciada = False
        return io.BytesIO(b"audio-falso")

    def cancelar(self):
        self.iniciada = False
        self.cancelada = True


class MotorFalso:
    """Devuelve, en orden, las respuestas que se le hayan cargado."""

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = 0
        self.mensajes_recibidos = []

    def responder(self, mensajes, herramientas=None, **kwargs):
        self.llamadas += 1
        self.mensajes_recibidos.append(mensajes)
        if not self.respuestas:
            raise AssertionError(
                "el motor falso se quedo sin respuestas: la prueba esperaba menos "
                "llamadas al modelo de las que hubo"
            )
        siguiente = self.respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


class VozFalsa:
    def __init__(self, fallo=None):
        self.fallo = fallo
        self.dicho = []

    def __call__(self, texto):
        if self.fallo:
            raise self.fallo
        self.dicho.append(texto)


def _texto(contenido):
    return RespuestaDelModelo(texto=contenido)


def _con_tool(nombre="estado_laptop", identificador="call-1", texto=""):
    return RespuestaDelModelo(
        texto=texto,
        peticiones_de_tool=[PeticionDeTool(id=identificador, nombre=nombre, argumentos={})],
        mensaje_crudo={"role": "assistant", "content": texto, "tool_calls": [
            {"id": identificador, "type": "function",
             "function": {"name": nombre, "arguments": "{}"}}
        ]},
    )


class Recolector:
    """Guarda los eventos que el orquestador manda a la GUI."""

    def __init__(self, al_recibir=None):
        self.eventos = []
        self._al_recibir = al_recibir

    def __call__(self, evento: Evento):
        self.eventos.append(evento)
        if self._al_recibir:
            self._al_recibir(evento)

    @property
    def estados(self):
        return [e.estado for e in self.eventos if e.tipo is TipoEvento.ESTADO]

    @property
    def errores(self):
        return [e.texto for e in self.eventos if e.tipo is TipoEvento.ERROR]

    def textos(self, tipo):
        return [e.texto for e in self.eventos if e.tipo is tipo]


# En las pruebas el aviso dura casi nada: lo que se verifica es que la transicion
# ocurra y que se pueda ver, no cuantos segundos exactos. Con 2.5 s reales la suite
# tardaria medio minuto en vez de tres segundos.
ESPERA_DEL_AVISO = 0.05


def _armar(transcripcion="hola", respuestas=None, voz=None, grabadora=None,
           ejecutar_herramienta=None, limite_rondas_tool=2, herramientas=None,
           segundos_en_atencion=ESPERA_DEL_AVISO):
    recolector = Recolector()
    memoria = MemoriaConversacional(system_prompt="sistema", max_turnos=10)
    orquestador = Orquestador(
        grabadora=grabadora or GrabadoraFalsa(),
        transcriptor=(transcripcion if callable(transcripcion)
                      else (lambda audio: transcripcion)),
        motor=MotorFalso(respuestas if respuestas is not None else [_texto("hola a ti")]),
        voz=voz or VozFalsa(),
        memoria=memoria,
        notificar=recolector,
        herramientas=herramientas,
        ejecutar_herramienta=ejecutar_herramienta,
        limite_rondas_tool=limite_rondas_tool,
        segundos_en_atencion=segundos_en_atencion,
    )
    return orquestador, recolector, memoria


def _turno_completo(orquestador):
    assert orquestador.empezar_a_escuchar() is True
    orquestador.terminar_y_responder()
    orquestador.esperar(ESPERA_MAXIMA)
    assert not orquestador.ocupado, "el hilo trabajador no termino: se colgo el turno"


# --- Turno feliz -----------------------------------------------------------

def test_turno_completo_recorre_los_estados_en_orden():
    orquestador, recolector, _ = _armar()

    _turno_completo(orquestador)

    assert recolector.estados == [
        Estado.ESCUCHANDO,
        Estado.PENSANDO,
        Estado.RESPONDIENDO,
        Estado.REPOSO,
    ]
    assert orquestador.estado is Estado.REPOSO


def test_el_turno_avisa_lo_transcrito_y_lo_respondido():
    orquestador, recolector, _ = _armar(
        transcripcion="que hora es", respuestas=[_texto("Son las tres.")]
    )

    _turno_completo(orquestador)

    assert recolector.textos(TipoEvento.TRANSCRIPCION) == ["que hora es"]
    assert recolector.textos(TipoEvento.RESPUESTA) == ["Son las tres."]


def test_el_turno_queda_guardado_en_la_memoria():
    orquestador, _, memoria = _armar(
        transcripcion="hola", respuestas=[_texto("hola a ti")]
    )

    _turno_completo(orquestador)

    contenidos = [m["content"] for m in memoria.mensajes()]
    assert contenidos == ["sistema", "hola", "hola a ti"]


def test_la_respuesta_se_dice_en_voz_alta():
    voz = VozFalsa()
    orquestador, _, _ = _armar(respuestas=[_texto("Buenas tardes.")], voz=voz)

    _turno_completo(orquestador)

    assert voz.dicho == ["Buenas tardes."]


def test_el_hilo_trabajador_es_efimero():
    """Termina solo, sin que nadie lo detenga: no queda ningun hilo vivo entre turnos."""
    orquestador, _, _ = _armar()

    _turno_completo(orquestador)
    assert not orquestador.ocupado

    # Y un segundo turno arranca sin problema, con un hilo nuevo.
    orquestador._motor = MotorFalso([_texto("otra vez")])
    _turno_completo(orquestador)
    assert not orquestador.ocupado


# --- De ATENCION siempre se vuelve a REPOSO --------------------------------

@pytest.mark.parametrize("descripcion,argumentos", [
    ("transcripcion vacia", {"transcripcion": ""}),
    ("solo espacios", {"transcripcion": "   "}),
    ("respuesta vacia dos veces", {"respuestas": [_texto(""), _texto("")]}),
    ("fallo del modelo", {"respuestas": [ErrorDePruebaDelProyecto("El modelo fallo.")]}),
    ("fallo de red", {"respuestas": [ErrorDePruebaDelProyecto("Revisa tu conexion.")]}),
])
def test_todo_fallo_pasa_por_atencion_y_termina_en_reposo(descripcion, argumentos):
    orquestador, recolector, _ = _armar(**argumentos)

    _turno_completo(orquestador)

    assert Estado.ATENCION in recolector.estados, descripcion
    assert recolector.estados[-1] is Estado.REPOSO, descripcion
    assert orquestador.estado is Estado.REPOSO, descripcion
    assert recolector.errores, "un fallo siempre debe avisar con un mensaje"


def test_una_respuesta_vacia_se_reintenta_una_sola_vez():
    """Seccion 13 del diseno: reintento unico, y si vuelve vacia, mensaje.

    Una respuesta vacia suele ser un tropiezo puntual del modelo. Reintentar una vez
    salva el turno; reintentar sin limite dejaria a la usuaria esperando y gastando
    saldo delante del tribunal.
    """
    orquestador, recolector, _ = _armar(
        respuestas=[_texto(""), _texto("Ahora si: son las tres.")]
    )

    _turno_completo(orquestador)

    assert orquestador._motor.llamadas == 2
    assert recolector.textos(TipoEvento.RESPUESTA) == ["Ahora si: son las tres."]
    assert Estado.ATENCION not in recolector.estados, "el reintento salvo el turno"


def test_dos_respuestas_vacias_seguidas_terminan_en_mensaje():
    orquestador, recolector, _ = _armar(respuestas=[_texto(""), _texto("")])

    _turno_completo(orquestador)

    assert orquestador._motor.llamadas == 2, "no debe reintentar mas de una vez"
    assert recolector.errores
    assert recolector.estados[-1] is Estado.REPOSO


def test_la_transcripcion_vacia_da_un_mensaje_amable_y_no_una_traza():
    orquestador, recolector, _ = _armar(transcripcion="")

    _turno_completo(orquestador)

    assert recolector.errores == ["No te escuche bien. Intenta de nuevo, por favor."]


def test_un_error_inesperado_no_muestra_detalles_tecnicos():
    """Una excepcion ajena al proyecto no debe filtrar su texto a la pantalla."""
    orquestador, recolector, _ = _armar(
        respuestas=[ZeroDivisionError("division by zero en la linea 42")]
    )

    _turno_completo(orquestador)

    assert "division by zero" not in " ".join(recolector.errores)
    assert recolector.errores  # pero si hay un mensaje generico
    assert orquestador.estado is Estado.REPOSO


def test_un_error_del_proyecto_si_muestra_su_mensaje_redactado():
    orquestador, recolector, _ = _armar(
        respuestas=[ErrorDePruebaDelProyecto("Revisa tu conexion a internet.")]
    )

    _turno_completo(orquestador)

    assert recolector.errores == ["Revisa tu conexion a internet."]


def test_ninguna_excepcion_escapa_del_hilo_trabajador():
    """Si escapara, el hilo moriria sin devolver el estado y la app quedaria muda."""
    class TranscriptorExplosivo:
        def __call__(self, audio):
            raise RuntimeError("boom")

    orquestador, recolector, _ = _armar(transcripcion=TranscriptorExplosivo())

    _turno_completo(orquestador)

    assert orquestador.estado is Estado.REPOSO
    assert recolector.errores


# --- Fallos del microfono (ocurren en el hilo de la GUI) -------------------

def test_si_el_microfono_no_abre_no_se_lanza_excepcion_a_la_gui():
    grabadora = GrabadoraFalsa(
        fallo_al_iniciar=ErrorDePruebaDelProyecto("Revisa el microfono.")
    )
    orquestador, recolector, _ = _armar(grabadora=grabadora)

    assert orquestador.empezar_a_escuchar() is False
    assert recolector.errores == ["Revisa el microfono."]
    orquestador.esperar(ESPERA_MAXIMA)
    assert orquestador.estado is Estado.REPOSO


def test_si_falla_al_detener_el_turno_no_arranca():
    grabadora = GrabadoraFalsa(
        fallo_al_detener=ErrorDePruebaDelProyecto("No se capturo audio.")
    )
    orquestador, recolector, _ = _armar(grabadora=grabadora)

    orquestador.empezar_a_escuchar()
    orquestador.terminar_y_responder()

    assert not orquestador.ocupado, "no debe lanzarse ningun hilo si no hay audio"
    assert recolector.errores == ["No se capturo audio."]
    orquestador.esperar(ESPERA_MAXIMA)
    assert orquestador.estado is Estado.REPOSO


def test_no_se_puede_hablar_encima_de_un_turno_en_vuelo():
    """Pulsar el boton mientras el asistente responde no debe abrir el microfono.

    La voz se bloquea a proposito hasta que la prueba la libera: asi el turno esta
    garantizadamente en vuelo cuando se intenta el segundo, sin depender de tiempos.
    """
    import threading

    puede_terminar = threading.Event()

    class VozQueEspera:
        def __call__(self, texto):
            puede_terminar.wait(ESPERA_MAXIMA)

    grabadora = GrabadoraFalsa()
    orquestador, recolector, _ = _armar(voz=VozQueEspera(), grabadora=grabadora)
    orquestador.empezar_a_escuchar()
    orquestador.terminar_y_responder()

    try:
        assert orquestador.empezar_a_escuchar() is False
        assert recolector.errores
        assert not grabadora.iniciada, "el microfono no debe reabrirse a mitad de turno"
    finally:
        puede_terminar.set()
        orquestador.esperar(ESPERA_MAXIMA)


def test_cancelar_la_escucha_vuelve_a_reposo_sin_procesar():
    grabadora = GrabadoraFalsa()
    orquestador, recolector, memoria = _armar(grabadora=grabadora)

    orquestador.empezar_a_escuchar()
    orquestador.cancelar_escucha()

    assert grabadora.cancelada
    assert orquestador.estado is Estado.REPOSO
    assert memoria.numero_de_turnos() == 0


# --- Voz: falla sin perder el turno ----------------------------------------

def test_si_la_voz_falla_la_respuesta_ya_se_mostro_y_se_vuelve_a_reposo():
    voz = VozFalsa(fallo=ErrorDePruebaDelProyecto("No se pudo reproducir la voz."))
    orquestador, recolector, memoria = _armar(
        respuestas=[_texto("Aqui esta tu respuesta.")], voz=voz
    )

    _turno_completo(orquestador)

    assert recolector.textos(TipoEvento.RESPUESTA) == ["Aqui esta tu respuesta."]
    assert "No se pudo reproducir la voz." in recolector.errores
    assert recolector.estados[-1] is Estado.REPOSO
    # El turno NO se pierde: queda en la memoria de la conversacion.
    assert "Aqui esta tu respuesta." in [m["content"] for m in memoria.mensajes()]


# --- Tool calling -----------------------------------------------------------

def test_ejecuta_la_herramienta_y_vuelve_a_preguntar_al_modelo():
    ejecutadas = []

    def ejecutar(peticion):
        ejecutadas.append(peticion.nombre)
        return "bateria al 87 por ciento"

    orquestador, recolector, memoria = _armar(
        respuestas=[_con_tool("estado_laptop"), _texto("Tienes 87 % de bateria.")],
        ejecutar_herramienta=ejecutar,
    )

    _turno_completo(orquestador)

    assert ejecutadas == ["estado_laptop"]
    assert recolector.textos(TipoEvento.HERRAMIENTA) == ["estado_laptop"]
    assert recolector.textos(TipoEvento.RESPUESTA) == ["Tienes 87 % de bateria."]
    roles = [m["role"] for m in memoria.mensajes()]
    assert roles == ["system", "user", "assistant", "tool", "assistant"]


def test_se_respeta_el_limite_de_rondas_de_tool_calling():
    """Un modelo que insiste en pedir herramientas no puede girar para siempre."""
    def ejecutar(peticion):
        return "resultado"

    # Cuatro respuestas seguidas pidiendo herramienta: con limite 2, el orquestador
    # debe llamar al modelo 3 veces (la inicial + 2 rondas) y quedarse con lo que haya.
    orquestador, recolector, _ = _armar(
        respuestas=[
            _con_tool(identificador="call-1", texto="voy a revisar"),
            _con_tool(identificador="call-2", texto="sigo revisando"),
            _con_tool(identificador="call-3", texto="ya casi"),
            _con_tool(identificador="call-4", texto="listo"),
        ],
        ejecutar_herramienta=ejecutar,
        limite_rondas_tool=2,
    )

    _turno_completo(orquestador)

    assert orquestador._motor.llamadas == 3
    assert recolector.textos(TipoEvento.RESPUESTA) == ["ya casi"]
    assert orquestador.estado is Estado.REPOSO


def test_sin_ejecutor_de_herramientas_se_responde_con_el_texto_disponible():
    """Antes de T-15 no hay herramientas: pedirlas no debe romper el turno."""
    orquestador, recolector, _ = _armar(
        respuestas=[_con_tool(texto="Dejame ver eso.")],
        ejecutar_herramienta=None,
    )

    _turno_completo(orquestador)

    assert recolector.textos(TipoEvento.RESPUESTA) == ["Dejame ver eso."]
    assert orquestador.estado is Estado.REPOSO


def test_si_una_herramienta_falla_se_le_informa_al_modelo_y_el_turno_sigue():
    def ejecutar(peticion):
        raise ErrorDePruebaDelProyecto("No se pudo leer la bateria.")

    orquestador, recolector, memoria = _armar(
        respuestas=[_con_tool("estado_laptop"), _texto("No pude revisar la bateria.")],
        ejecutar_herramienta=ejecutar,
    )

    _turno_completo(orquestador)

    mensaje_de_tool = [m for m in memoria.mensajes() if m["role"] == "tool"][0]
    assert "No se pudo leer la bateria." in mensaje_de_tool["content"]
    assert recolector.textos(TipoEvento.RESPUESTA) == ["No pude revisar la bateria."]
    assert orquestador.estado is Estado.REPOSO


# --- El canal hacia la GUI --------------------------------------------------

def test_un_fallo_de_la_gui_no_tumba_el_turno():
    """Si el callback de la interfaz revienta, el turno debe terminar igual."""
    def notificar_roto(evento):
        raise RuntimeError("la ventana ya se cerro")

    memoria = MemoriaConversacional(system_prompt="sistema", max_turnos=10)
    orquestador = Orquestador(
        grabadora=GrabadoraFalsa(),
        transcriptor=lambda audio: "hola",
        motor=MotorFalso([_texto("hola a ti")]),
        voz=VozFalsa(),
        memoria=memoria,
        notificar=notificar_roto,
    )

    orquestador.empezar_a_escuchar()
    orquestador.terminar_y_responder()
    orquestador.esperar(ESPERA_MAXIMA)

    assert not orquestador.ocupado
    assert orquestador.estado is Estado.REPOSO


def test_el_orquestador_no_importa_nada_de_la_gui():
    """La regla estructural de T-09, verificada sobre el codigo fuente.

    Si alguien anadiera un import de tkinter o de gui/, esta prueba lo detiene: es
    justo el cambio que produce cuelgues intermitentes imposibles de reproducir.
    """
    import ast
    from pathlib import Path

    fuente = Path(__file__).resolve().parents[1] / "core" / "orchestrator.py"
    arbol = ast.parse(fuente.read_text(encoding="utf-8"))

    importados = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados += [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            importados.append(nodo.module or "")

    prohibidos = [m for m in importados
                  if m.startswith(("tkinter", "customtkinter", "gui"))]
    assert prohibidos == [], f"el orquestador no debe conocer la GUI: {prohibidos}"


# --- El aviso tiene que durar lo suficiente para verse ---------------------

def test_el_estado_de_atencion_se_queda_a_la_vista_antes_de_volver_a_reposo():
    """Defecto detectado al probar la aplicacion: el aviso ocurria pero nadie lo veia.

    Las dos transiciones pasaban en la misma linea, asi que ATENCION duraba
    microsegundos. La maquina de estados era correcta y aun asi el indicador nunca se
    ponia en durazno. Aqui se comprueba que ATENCION llega ANTES y REPOSO despues, y
    que entre ambos pasa tiempo de verdad.
    """
    import time

    orquestador, recolector, _ = _armar(transcripcion="", segundos_en_atencion=0.3)

    assert orquestador.empezar_a_escuchar() is True
    orquestador.terminar_y_responder()
    orquestador._hilo.join(ESPERA_MAXIMA)

    # Justo despues del fallo, el indicador debe estar en ATENCION, no en reposo.
    assert orquestador.estado is Estado.ATENCION
    assert recolector.estados[-1] is Estado.ATENCION

    inicio = time.perf_counter()
    orquestador.esperar(ESPERA_MAXIMA)
    transcurrido = time.perf_counter() - inicio

    assert orquestador.estado is Estado.REPOSO
    assert recolector.estados[-1] is Estado.REPOSO
    assert transcurrido > 0.1, "la vuelta a reposo fue instantanea otra vez"


def test_hablar_de_nuevo_cancela_el_aviso_pendiente():
    """Si la usuaria vuelve a hablar, el aviso se da por leido y no pisa la escucha.

    El primer turno falla (no se escucho nada) y deja el aviso en pantalla con un
    temporizador largo. El segundo turno si trae voz: el temporizador viejo no debe
    aterrizar a mitad de camino y mandar el indicador a reposo mientras se escucha.
    """
    turnos = iter(["", "ahora si te escucho"])
    orquestador, recolector, _ = _armar(
        transcripcion=lambda audio: next(turnos),
        respuestas=[_texto("perfecto")],
        segundos_en_atencion=5,
    )

    orquestador.empezar_a_escuchar()
    orquestador.terminar_y_responder()
    orquestador._hilo.join(ESPERA_MAXIMA)
    assert orquestador.estado is Estado.ATENCION

    assert orquestador.empezar_a_escuchar() is True
    assert orquestador.estado is Estado.ESCUCHANDO, (
        "empezar a escuchar debe cancelar el aviso pendiente"
    )

    orquestador.terminar_y_responder()
    orquestador._hilo.join(ESPERA_MAXIMA)

    assert orquestador.estado is Estado.REPOSO
    assert recolector.textos(TipoEvento.RESPUESTA) == ["perfecto"]
