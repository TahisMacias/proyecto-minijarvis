"""Pruebas del push-to-talk por teclado (defecto detectado al probar, 2026-08-14).

EL DEFECTO: mantener presionada la barra espaciadora no servia para hablar. La causa
es la repeticion automatica de teclas del sistema. Mientras una tecla sigue hundida,
el sistema la repite, y segun la maquina esa repeticion llega de dos formas distintas:

  a) una ristra de KeyPress sueltos  -> inofensiva, basta con ignorar los repetidos;
  b) PAREJAS de KeyRelease + KeyPress decenas de veces por segundo -> destructiva: el
     KeyRelease falso cerraba el microfono a los milisegundos de abrirlo, asi que la
     usuaria hablaba y no se grababa nada.

La correccion es no creerle a un KeyRelease de inmediato: se agenda el cierre y, si
llega otro KeyPress dentro del margen, era repeticion y se cancela.

Estas pruebas NO abren ninguna ventana. Se construye el objeto sin inicializar Tk y se
le inyecta un reloj falso en lugar de `after`, para que la suite siga corriendo en
cualquier maquina, con o sin pantalla, y sin depender de tiempos reales.
"""

from gui.desktop_app import MILIS_ANTIRREBOTE_ESPACIO, AplicacionMiniJarvis


class VentanaDePrueba(AplicacionMiniJarvis):
    """La ventana real, pero sin Tk: solo la logica de la barra espaciadora.

    Se salta `__init__` a proposito (crearia una ventana de verdad) y se reemplazan
    `after` y `after_cancel` por un reloj de mentira que la prueba adelanta a mano.
    """

    def __init__(self):  # noqa: D107 - no se llama al de la clase madre
        self._espacio_presionado = False
        self._cierre_de_espacio_pendiente = None
        self.acciones = []
        self._agendado = {}
        self._siguiente_id = 0

    # --- Reloj falso -------------------------------------------------------

    def after(self, milis, funcion=None, *args):
        self._siguiente_id += 1
        self._agendado[self._siguiente_id] = (funcion, args)
        return self._siguiente_id

    def after_cancel(self, identificador):
        self._agendado.pop(identificador, None)

    def correr_el_reloj(self):
        """Ejecuta lo que quedo agendado, como haria Tkinter al pasar el tiempo."""
        pendientes, self._agendado = self._agendado, {}
        for funcion, args in pendientes.values():
            funcion(*args)

    # --- Lo que hace la ventana de verdad ----------------------------------

    def _al_presionar(self, evento=None):
        self.acciones.append("abrir microfono")

    def _al_soltar(self, evento=None):
        self.acciones.append("cerrar y responder")


def _mantener_con_repeticion_en_parejas(ventana, repeticiones):
    """Forma (b): la destructiva. Cada repeticion trae un KeyRelease falso."""
    ventana._al_presionar_espacio()
    for _ in range(repeticiones):
        ventana._al_soltar_espacio()
        ventana._al_presionar_espacio()


def test_mantener_la_barra_abre_el_microfono_una_sola_vez():
    ventana = VentanaDePrueba()

    _mantener_con_repeticion_en_parejas(ventana, repeticiones=15)

    assert ventana.acciones == ["abrir microfono"], (
        "con la repeticion en parejas el microfono se cerraba solo, y la usuaria "
        "hablaba sin que se grabara nada"
    )


def test_al_soltar_de_verdad_el_turno_arranca():
    ventana = VentanaDePrueba()

    _mantener_con_repeticion_en_parejas(ventana, repeticiones=15)
    ventana._al_soltar_espacio()
    ventana.correr_el_reloj()  # pasa el margen sin ninguna repeticion nueva

    assert ventana.acciones == ["abrir microfono", "cerrar y responder"]
    assert not ventana._espacio_presionado


def test_la_repeticion_de_solo_keypress_tampoco_reabre_el_microfono():
    """Forma (a): la inofensiva. Debe seguir funcionando igual."""
    ventana = VentanaDePrueba()

    ventana._al_presionar_espacio()
    for _ in range(15):
        ventana._al_presionar_espacio()
    ventana._al_soltar_espacio()
    ventana.correr_el_reloj()

    assert ventana.acciones == ["abrir microfono", "cerrar y responder"]


def test_un_toque_corto_tambien_completa_el_turno():
    """Presionar y soltar rapido: sigue siendo un turno valido, aunque salga corto."""
    ventana = VentanaDePrueba()

    ventana._al_presionar_espacio()
    ventana._al_soltar_espacio()
    ventana.correr_el_reloj()

    assert ventana.acciones == ["abrir microfono", "cerrar y responder"]


def test_dos_turnos_seguidos_por_teclado():
    ventana = VentanaDePrueba()

    for _ in range(2):
        ventana._al_presionar_espacio()
        ventana._al_soltar_espacio()
        ventana.correr_el_reloj()

    assert ventana.acciones == [
        "abrir microfono", "cerrar y responder",
        "abrir microfono", "cerrar y responder",
    ]


def test_un_keyrelease_suelto_sin_haber_presionado_no_hace_nada():
    """Puede llegar si la ventana toma el foco con la tecla ya hundida."""
    ventana = VentanaDePrueba()

    ventana._al_soltar_espacio()
    ventana.correr_el_reloj()

    assert ventana.acciones == []


def test_el_margen_de_antirrebote_es_mas_corto_que_un_dedo_humano():
    """60 ms: la repeticion del sistema cae dentro; soltar y volver a pulsar, no."""
    assert 20 <= MILIS_ANTIRREBOTE_ESPACIO <= 120
