"""Memoria conversacional de Mini-JARVIS (tarea T-04).

Guarda el historial de la conversacion en el formato de mensajes que espera la API
del LLM (una lista de diccionarios con "role" y "content") y lo recorta cuando se
hace demasiado largo.

POR QUE EXISTE ESTE MODULO SEPARADO DEL MOTOR DEL LLM: un modelo de lenguaje no
recuerda nada entre una llamada y la siguiente. La ilusion de que "se acuerda" de lo
que dijimos hace tres frases se consigue reenviandole toda la conversacion completa
en cada peticion. Pero esa conversacion no puede crecer para siempre: cada modelo
tiene una ventana de contexto maxima, y ademas se paga por token enviado. Por eso
hace falta una politica explicita de que se conserva y que se descarta.

POLITICA ELEGIDA (seccion 8 del documento de diseno): se conservan los ultimos
MAX_TURNOS_MEMORIA turnos y el system prompt NUNCA se descarta. Al superar el limite
se descarta el turno mas antiguo, no el mas nuevo: lo que se acaba de decir es
siempre lo mas relevante para la respuesta que viene.

Se trunca por TURNOS y no por tokens a proposito. Truncar por tokens seria mas
eficiente, pero el resultado dependeria del tokenizador y seria dificil de predecir
y de verificar. Truncar por turnos es predecible, se demuestra en vivo durante la
sustentacion y se prueba entero sin llamar a ninguna API.

ESTE MODULO NO IMPORTA config.py, y es deliberado: la tabla de modulos del diseno
(seccion 6) lo lista sin dependencias. El system prompt y el limite de turnos se
reciben como argumentos obligatorios, sin valor por defecto. Dos consecuencias
buenas: no se duplica aqui ninguna constante que config.py ya define como fuente
unica de verdad, y las pruebas corren en una maquina sin `.env` ni credenciales,
que es justamente lo que se pide de un gate determinista.

Quien construye la memoria en la aplicacion real (el orquestador, T-09) si importa
config.py y le pasa `config.MAX_TURNOS_MEMORIA`.
"""

from __future__ import annotations

import copy


# Divisor para la estimacion rapida de tokens. Regla practica ampliamente usada: en
# espanol, un token equivale aproximadamente a 4 caracteres. Es una ESTIMACION para
# el indicador visual de la GUI, no una medida exacta: la cuenta real la hace el
# proveedor del modelo con su propio tokenizador. Se documenta el numero aqui para
# que nadie lo confunda con un dato exacto.
CARACTERES_POR_TOKEN_APROX = 4


class MemoriaConversacional:
    """Historial de la conversacion con truncado por turnos.

    Un TURNO es un mensaje de la usuaria mas todo lo que el asistente produjo en
    respuesta: su respuesta final y, si hubo tool calling, los mensajes intermedios
    de rol "tool". Se agrupa asi, y no mensaje por mensaje, porque descartar la
    pregunta de la usuaria y dejar huerfana la respuesta del asistente (o al reves)
    le daria al modelo un historial incoherente.
    """

    def __init__(self, system_prompt: str, max_turnos: int) -> None:
        if max_turnos < 1:
            raise ValueError(
                f"max_turnos debe ser al menos 1; se recibio {max_turnos}. Una "
                "memoria de cero turnos no podria sostener ni la pregunta actual."
            )
        self.system_prompt = system_prompt
        self.max_turnos = max_turnos
        # Cada elemento de esta lista es un turno: una lista de mensajes que empieza
        # con el mensaje de la usuaria.
        self._turnos: list[list[dict]] = []

    # --- Escritura ---------------------------------------------------------

    def agregar_usuario(self, texto: str) -> None:
        """Abre un turno nuevo con lo que dijo la usuaria y aplica el truncado."""
        self._turnos.append([{"role": "user", "content": texto}])
        self._truncar()

    def agregar_asistente(self, texto: str) -> None:
        """Cierra el turno abierto con la respuesta del asistente."""
        self._mensaje_al_turno_abierto({"role": "assistant", "content": texto})

    def agregar_mensaje_del_asistente_crudo(self, mensaje: dict) -> None:
        """Anade el mensaje del asistente tal cual lo devolvio la API.

        Hace falta cuando el modelo pidio una herramienta: la API exige que cada
        mensaje de rol "tool" venga precedido por el mensaje del asistente que la
        pidio, con sus `tool_calls` intactos. Si se guardara solo el texto, la
        siguiente llamada seria rechazada por incoherente.
        """
        if not mensaje:
            return
        self._mensaje_al_turno_abierto(dict(mensaje))

    def agregar_mensaje_de_tool(self, tool_call_id: str, contenido: str) -> None:
        """Anade al turno abierto el resultado de una herramienta (T-15).

        Va dentro del mismo turno que la pregunta que lo provoco: si se descartara
        por separado, el modelo veria el resultado de una herramienta sin saber que
        se le pregunto, o una peticion de herramienta sin su resultado.
        """
        self._mensaje_al_turno_abierto(
            {"role": "tool", "tool_call_id": tool_call_id, "content": contenido}
        )

    def _mensaje_al_turno_abierto(self, mensaje: dict) -> None:
        if not self._turnos:
            raise ValueError(
                "No hay ningun turno abierto: el historial debe empezar siempre por "
                "un mensaje de la usuaria. Llama antes a agregar_usuario()."
            )
        self._turnos[-1].append(mensaje)

    def _truncar(self) -> None:
        """Descarta turnos completos desde el mas antiguo hasta respetar el limite.

        Se usa un bucle y no un solo descarte porque asi la invariante se cumple
        aunque alguien reduzca max_turnos en caliente o cargue varios turnos de golpe.
        """
        while len(self._turnos) > self.max_turnos:
            self._turnos.pop(0)

    def limpiar(self) -> None:
        """Borra la conversacion. El system prompt sobrevive: no es conversacion."""
        self._turnos = []

    # --- Lectura -----------------------------------------------------------

    def mensajes(self) -> list[dict]:
        """Devuelve el historial listo para enviar al LLM.

        El system prompt va siempre primero y siempre esta presente, sin importar
        cuantos turnos se hayan descartado: es lo que define quien es el asistente.

        Se devuelve una copia profunda a proposito. Si devolvieramos la lista
        interna, quien la reciba podria modificar el historial de la memoria sin
        querer (por ejemplo el motor del LLM al anadir el manifest de herramientas)
        y el truncado dejaria de ser la unica via de cambio.
        """
        historial = [{"role": "system", "content": self.system_prompt}]
        for turno in self._turnos:
            historial.extend(turno)
        return copy.deepcopy(historial)

    def numero_de_turnos(self) -> int:
        """Turnos vivos en memoria. Lo muestra el indicador de la GUI (T-14)."""
        return len(self._turnos)

    def esta_llena(self) -> bool:
        """True si el proximo turno hara que se descarte el mas antiguo.

        La GUI lo usa para avisar visualmente antes de que ocurra el descarte, que
        es justo lo que se quiere poder senalar durante la sustentacion oral.
        """
        return len(self._turnos) >= self.max_turnos

    def estimar_tokens(self) -> int:
        """Estimacion del tamano del historial en tokens, para el indicador visual.

        ES UNA ESTIMACION, no una medida. Cuenta los caracteres de todo lo que se
        enviaria al modelo (system prompt incluido) y divide por
        CARACTERES_POR_TOKEN_APROX. El numero exacto solo lo sabe el tokenizador del
        modelo; para una barra de progreso en pantalla, esta aproximacion basta y no
        cuesta ni una llamada de red ni la descarga de un tokenizador.
        """
        caracteres = sum(
            len(str(mensaje.get("content", ""))) for mensaje in self.mensajes()
        )
        return caracteres // CARACTERES_POR_TOKEN_APROX
