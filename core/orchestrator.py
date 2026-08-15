"""Orquestador y maquina de estados (tarea T-09).

Es el director de orquesta del turno de voz: manda a grabar, a transcribir, a pensar
y a hablar, en ese orden, y va avisando en que estado esta el asistente.

LAS DOS REGLAS QUE NO SE NEGOCIAN
=================================

1. UN HILO TRABAJADOR EFIMERO POR TURNO. Nace cuando la usuaria suelta el boton y
   muere cuando la respuesta termino de sonar. No hay bucle `asyncio` de larga vida
   ni hilos permanentes (seccion 5 del diseno). Un turno tarda varios segundos entre
   subir audio, esperar al modelo y sintetizar voz; hacer eso en el hilo de la
   interfaz congelaria la ventana por completo, que es exactamente el fallo que el
   enunciado prohibe.

2. NINGUN HILO TRABAJADOR TOCA UN WIDGET. Tkinter no es seguro entre hilos: modificar
   una etiqueta desde otro hilo produce cuelgues intermitentes, de los que aparecen
   una vez de cada veinte y justo el dia de la sustentacion. Por eso este modulo
   **no importa nada de la GUI**. Su unico canal de salida es una funcion
   `notificar(evento)` que recibe en el constructor. La GUI entrega una funcion que
   se limita a reenviar el evento con `root.after(0, ...)`, que es la unica forma
   segura de cruzar de un hilo cualquiera al hilo de la interfaz:

       orquestador = Orquestador(..., notificar=lambda ev: root.after(0, self._pintar, ev))

   Escrito asi, la regla se cumple por construccion: aunque alguien quisiera tocar un
   widget desde aqui, no tiene ninguno a mano.

NINGUNA EXCEPCION SUBE AL MAINLOOP. Todo el trabajo del hilo va envuelto en un
manejo de errores que termina siempre en un evento de error y en el estado REPOSO.
Una excepcion que escape de un hilo trabajador no la puede atrapar el `mainloop`:
la aplicacion no se cierra, pero se queda muda y "pensando" para siempre. Eso es
peor que un mensaje de error, porque no se puede diagnosticar en vivo.

MAQUINA DE ESTADOS (seccion 11 del diseno)

    REPOSO -> ESCUCHANDO -> PENSANDO -> RESPONDIENDO -> REPOSO
                  |             |            |
                  +-------------+------------+--> ATENCION -> REPOSO

ATENCION es el estado de "algo no salio": de el SIEMPRE se vuelve a REPOSO, nunca se
queda ahi. Es la garantia de que la aplicacion siempre puede intentar otro turno.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum


class Estado(Enum):
    """Los cinco estados del asistente. La GUI pinta color y forma segun este valor."""

    REPOSO = "REPOSO"
    ESCUCHANDO = "ESCUCHANDO"
    PENSANDO = "PENSANDO"
    RESPONDIENDO = "RESPONDIENDO"
    ATENCION = "ATENCION"


class TipoEvento(Enum):
    """Que clase de noticia le llega a la interfaz."""

    ESTADO = "ESTADO"                # cambio de estado; trae `estado`
    TRANSCRIPCION = "TRANSCRIPCION"  # lo que se entendio que dijo la usuaria
    RESPUESTA = "RESPUESTA"          # el texto que el asistente va a decir
    HERRAMIENTA = "HERRAMIENTA"      # se uso una herramienta; para el panel de la GUI
    ERROR = "ERROR"                  # mensaje amable, ya redactado para mostrarse


@dataclass
class Evento:
    """Lo unico que este modulo le manda a la interfaz. Datos, nunca widgets."""

    tipo: TipoEvento
    texto: str = ""
    estado: Estado | None = None


class Orquestador:
    """Coordina un turno completo de voz.

    Todas las piezas se reciben por parametro (grabadora, transcriptor, motor, voz,
    memoria). No se construyen aqui dentro. Asi las pruebas pueden pasar dobles y
    verificar la maquina de estados entera sin microfono, sin red y sin gastar saldo,
    que es lo que exige el gate de esta tarea.
    """

    def __init__(self, grabadora, transcriptor, motor, voz, memoria, notificar,
                 herramientas=None, ejecutar_herramienta=None,
                 limite_rondas_tool: int = 2) -> None:
        self._grabadora = grabadora
        self._transcribir = transcriptor
        self._motor = motor
        self._voz = voz
        self._memoria = memoria
        self._notificar = notificar
        self._herramientas = herramientas
        self._ejecutar_herramienta = ejecutar_herramienta
        self._limite_rondas_tool = limite_rondas_tool

        self._estado = Estado.REPOSO
        self._hilo: threading.Thread | None = None
        # Protege el cambio de estado: lo leen el hilo de la GUI y el trabajador.
        self._candado = threading.Lock()

    # --- Estado -------------------------------------------------------------

    @property
    def estado(self) -> Estado:
        with self._candado:
            return self._estado

    @property
    def ocupado(self) -> bool:
        """True mientras haya un turno en vuelo. La GUI desactiva el boton con esto."""
        return self._hilo is not None and self._hilo.is_alive()

    def _ir_a(self, estado: Estado) -> None:
        with self._candado:
            self._estado = estado
        self._avisar(Evento(TipoEvento.ESTADO, estado=estado))

    def _avisar(self, evento: Evento) -> None:
        """Entrega un evento a la interfaz sin dejar que un fallo suyo rompa el turno.

        Si el callback de la GUI falla (una ventana ya cerrada, por ejemplo), el turno
        debe seguir su curso y terminar ordenadamente. Un error al PINTAR no es un
        error del turno.
        """
        try:
            self._notificar(evento)
        except Exception:  # noqa: BLE001 - la GUI no puede tumbar al orquestador
            pass

    def _fallar(self, mensaje: str) -> None:
        """Camino unico de fallo: mensaje amable, ATENCION y de vuelta a REPOSO.

        Todos los errores del turno pasan por aqui. Tener un solo camino es lo que
        garantiza la invariante de que de ATENCION siempre se vuelve a REPOSO.
        """
        self._avisar(Evento(TipoEvento.ERROR, texto=mensaje))
        self._ir_a(Estado.ATENCION)
        self._ir_a(Estado.REPOSO)

    # --- Push to talk (corre en el hilo de la GUI) ---------------------------

    def empezar_a_escuchar(self) -> bool:
        """Abre el microfono. Devuelve False si no se pudo, sin lanzar excepcion.

        Corre en el hilo de la interfaz porque abrir el microfono es inmediato. Aun
        asi no puede levantar nada: una excepcion aqui SI subiria al `mainloop`.
        """
        if self.ocupado:
            self._avisar(Evento(
                TipoEvento.ERROR,
                texto="Espera a que termine de responder antes de hablar de nuevo.",
            ))
            return False

        try:
            self._grabadora.iniciar()
        except Exception as excepcion:  # noqa: BLE001
            self._fallar(self._mensaje_de(excepcion))
            return False

        self._ir_a(Estado.ESCUCHANDO)
        return True

    def terminar_y_responder(self) -> None:
        """Cierra el microfono y lanza el hilo trabajador del turno.

        El hilo es `daemon` para que cerrar la ventana no deje la aplicacion colgada
        esperando a que termine de hablar.
        """
        if self.estado is not Estado.ESCUCHANDO:
            return

        try:
            audio = self._grabadora.detener()
        except Exception as excepcion:  # noqa: BLE001
            self._fallar(self._mensaje_de(excepcion))
            return

        self._ir_a(Estado.PENSANDO)
        self._hilo = threading.Thread(
            target=self._procesar_turno,
            args=(audio,),
            name="minijarvis-turno",
            daemon=True,
        )
        self._hilo.start()

    def cancelar_escucha(self) -> None:
        """Aborta la grabacion en curso sin procesarla."""
        if self.estado is not Estado.ESCUCHANDO:
            return
        try:
            self._grabadora.cancelar()
        except Exception:  # noqa: BLE001 - cancelar nunca debe fallar hacia afuera
            pass
        self._ir_a(Estado.REPOSO)

    def esperar(self, timeout: float | None = None) -> None:
        """Bloquea hasta que el turno en vuelo termine. Solo para pruebas y cierre."""
        if self._hilo is not None:
            self._hilo.join(timeout)

    # --- El turno (corre en el hilo trabajador) -----------------------------

    def _procesar_turno(self, audio) -> None:
        """Todo el trabajo lento del turno. NUNCA deja escapar una excepcion."""
        try:
            # Se recorta aqui aunque el cliente de STT ya lo haga: una transcripcion
            # de puros espacios es indistinguible de una vacia para una persona, y el
            # orquestador no debe depender de la buena educacion de quien lo llama.
            texto_usuaria = (self._transcribir(audio) or "").strip()

            if not texto_usuaria:
                # Transcripcion vacia no es un error del sistema: es que no se
                # escucho nada. Se avisa con carino y se vuelve a reposo.
                self._fallar("No te escuche bien. Intenta de nuevo, por favor.")
                return

            self._avisar(Evento(TipoEvento.TRANSCRIPCION, texto=texto_usuaria))
            self._memoria.agregar_usuario(texto_usuaria)

            respuesta = self._conversar()
            texto_respuesta = (respuesta.texto or "").strip()

            if not texto_respuesta:
                self._fallar(
                    "Me quede sin palabras con esa. Intenta preguntarme de otra forma."
                )
                return

            self._memoria.agregar_asistente(texto_respuesta)
            self._avisar(Evento(TipoEvento.RESPUESTA, texto=texto_respuesta))

            self._ir_a(Estado.RESPONDIENDO)
            try:
                self._voz(texto_respuesta)
            except Exception as excepcion:  # noqa: BLE001
                # La voz es lo unico que puede fallar SIN perder el turno: la
                # respuesta ya esta en pantalla (seccion 13 del diseno).
                self._avisar(Evento(TipoEvento.ERROR, texto=self._mensaje_de(excepcion)))

            self._ir_a(Estado.REPOSO)

        except Exception as excepcion:  # noqa: BLE001 - ultima red de seguridad
            # Si algo llega hasta aqui es un fallo que no previmos. Aun asi, la
            # aplicacion queda utilizable: mensaje, ATENCION y REPOSO.
            self._fallar(self._mensaje_de(excepcion))

    def _conversar(self):
        """Pide respuesta al modelo, ejecutando herramientas hasta el limite de rondas.

        El limite existe para que un modelo que insista en pedir herramientas no deje
        el turno girando para siempre (y gastando saldo). Al agotarse las rondas se
        responde con el texto que haya, que es la regla de la seccion 7 del diseno.
        """
        rondas = 0
        while True:
            respuesta = self._motor.responder(
                self._memoria.mensajes(),
                herramientas=self._herramientas,
            )

            puede_ejecutar = (
                respuesta.pide_herramienta
                and self._ejecutar_herramienta is not None
                and rondas < self._limite_rondas_tool
            )
            if not puede_ejecutar:
                return respuesta

            rondas += 1
            self._memoria.agregar_mensaje_del_asistente_crudo(respuesta.mensaje_crudo)

            for peticion in respuesta.peticiones_de_tool:
                self._avisar(Evento(TipoEvento.HERRAMIENTA, texto=peticion.nombre))
                try:
                    resultado = self._ejecutar_herramienta(peticion)
                except Exception as excepcion:  # noqa: BLE001
                    # Que una herramienta falle no tumba el turno: se le informa al
                    # modelo del fallo y que el decida como responder.
                    resultado = f"La herramienta fallo: {self._mensaje_de(excepcion)}"
                self._memoria.agregar_mensaje_de_tool(peticion.id, str(resultado))

    # --- Traduccion de errores ----------------------------------------------

    @staticmethod
    def _mensaje_de(excepcion: BaseException) -> str:
        """Convierte una excepcion en algo que se le pueda mostrar a una persona.

        Los modulos de `core/` levantan errores tipados cuyo texto YA esta redactado
        para la usuaria; ese se usa tal cual. Cualquier otra excepcion (un fallo que
        no previmos) se reemplaza por un mensaje generico: una traza tecnica en
        pantalla no le sirve a nadie durante una demostracion, y ademas podria
        exponer detalles internos en un repositorio publico.
        """
        mensaje = str(excepcion).strip()
        if mensaje and _es_error_del_proyecto(excepcion):
            return mensaje
        return (
            "Algo no salio bien en ese turno. Vuelve a intentarlo; si sigue "
            "pasando, revisa la conexion a internet."
        )


def _es_error_del_proyecto(excepcion: BaseException) -> bool:
    """True si la excepcion viene de un modulo nuestro y su texto ya es presentable.

    Se comprueba por el modulo donde esta definida la clase y no con una lista de
    tipos importados, para no crear una dependencia circular entre el orquestador y
    cada modulo de core.
    """
    modulo = type(excepcion).__module__ or ""
    return modulo.startswith("core.")
