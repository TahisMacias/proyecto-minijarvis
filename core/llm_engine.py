"""Motor del modelo de lenguaje (tarea T-07).

Le manda al LLM el historial de la conversacion y devuelve lo que contesto: texto,
o la peticion de usar una herramienta.

LIMITE DE RESPONSABILIDAD, A PROPOSITO: este modulo **no ejecuta herramientas**.
Si el modelo pide `estado_laptop`, aqui solo se traduce esa peticion a un objeto
`PeticionDeTool` y se devuelve. Quien decide si esa herramienta se ejecuta, la
ejecuta y le devuelve el resultado al modelo es el orquestador (T-09). La razon es
de seguridad: el LLM no ejecuta codigo, solo emite JSON que otro modulo interpreta
contra una lista cerrada de herramientas. Mezclar ambas cosas en un mismo archivo
haria muy facil que manana alguien "ejecute lo que el modelo pida" sin filtro.

CAMBIO DE MODELO EN CALIENTE: el modelo es un atributo de la instancia, no una
constante congelada al importar. `cambiar_modelo()` lo reemplaza y la siguiente
respuesta ya sale del modelo nuevo, sin reiniciar la aplicacion. Es un requisito de
la sustentacion: se pide poder comparar Qwen y Llama en vivo.

MUESTREO: `temperatura` y `top_p` son parametros de cada llamada, no constantes.
Los sliders de la GUI (T-14) los leen y los mueven en vivo.
  - temperatura: que tan arriesgada es la eleccion de cada palabra. Cerca de 0 el
    modelo elige casi siempre la palabra mas probable y suena repetitivo pero
    predecible; mas alto, mas variedad y mas riesgo de decir algo raro.
  - top_p: de cuantas palabras candidatas elige. Con 0.9 descarta la cola de
    opciones improbables y reparte entre las que suman el 90 % de probabilidad.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import openai

from config import (
    MODELO_LLM_PREDETERMINADO,
    TEMPERATURA_PREDETERMINADA,
    TOGETHER_API_KEY,
    TOGETHER_BASE_URL,
    TOP_P_PREDETERMINADO,
)


# --- Identidad del asistente (seccion 12 del diseno) ------------------------
# La declaracion de ser una IA no es un adorno: la seccion 11 del enunciado la exige
# como consideracion etica. Se pone al inicio del prompt, no al final, porque es la
# instruccion que menos se debe diluir cuando la conversacion crece.
SYSTEM_PROMPT = (
    "Eres Mini-JARVIS, un asistente de voz en espanol. "
    "Eres una inteligencia artificial, no una persona: si te preguntan que eres, "
    "dilo con naturalidad, y ten presente que tus respuestas pueden contener "
    "errores, asi que no afirmes con seguridad lo que no sabes. "
    "Hablas con un tono calido, cercano y breve. "
    "Tus respuestas se van a LEER EN VOZ ALTA: escribe en frases cortas, sin listas "
    "con vinetas, sin tablas, sin emojis y sin formato de markdown, porque nada de "
    "eso se puede pronunciar. "
    "Responde en dos o tres frases salvo que te pidan explicitamente mas detalle. "
    "Cuando necesites datos de la computadora o informacion actual de internet, usa "
    "las herramientas disponibles en lugar de inventar el dato."
)


# --- Errores tipados --------------------------------------------------------

class ErrorDeLLM(RuntimeError):
    """Base de los fallos del modelo de lenguaje. La GUI atrapa esta."""


class SinConexionLLM(ErrorDeLLM):
    """No se pudo llegar al servidor: no hay red."""


class ModeloDemasiadoLento(ErrorDeLLM):
    """El servidor acepto la peticion pero no contesto a tiempo.

    Se separa de SinConexionLLM a proposito. Antes las dos cosas compartian mensaje y
    la aplicacion decia "revisa tu conexion a internet" cuando la conexion estaba
    perfecta: lo que pasaba era que el modelo tardaba mas que el tiempo de espera. Un
    mensaje de error que senala la causa equivocada es peor que no dar ninguno, porque
    manda a la usuaria a arreglar algo que no esta roto.
    """


class CredencialRechazadaLLM(ErrorDeLLM):
    """Clave invalida, cuenta sin saldo o limite de peticiones alcanzado."""


class RespuestaInvalida(ErrorDeLLM):
    """El servidor respondio con un error o con algo que no se pudo interpretar."""


TIMEOUT_SEGUNDOS = 90


# --- Estructuras de retorno -------------------------------------------------

@dataclass
class PeticionDeTool:
    """Una herramienta que el modelo quiere usar. Todavia NO se ha ejecutado nada."""

    id: str
    nombre: str
    argumentos: dict


@dataclass
class RespuestaDelModelo:
    """Lo que devolvio el modelo en un turno.

    `texto` y `peticiones_de_tool` no son excluyentes: un modelo puede acompanar la
    peticion de herramienta con una frase ("dejame revisar"). El orquestador decide
    que hacer con cada parte.
    """

    texto: str = ""
    peticiones_de_tool: list[PeticionDeTool] = field(default_factory=list)
    # Mensaje tal cual lo devolvio la API. El orquestador debe reenviarlo al historial
    # antes de los resultados de las herramientas: la API exige que cada mensaje de
    # rol "tool" venga precedido por el mensaje del asistente que lo pidio.
    mensaje_crudo: dict | None = None
    # Herramientas que el modelo pidio pero se descartaron por venir con argumentos
    # ilegibles. Se guardan para poder decirlo en la GUI, no para reintentarlas.
    tools_descartadas: list[str] = field(default_factory=list)

    @property
    def pide_herramienta(self) -> bool:
        return bool(self.peticiones_de_tool)


def _sin_credenciales(texto: str) -> str:
    """Elimina la clave de API de cualquier texto antes de mostrarlo (repo publico)."""
    if TOGETHER_API_KEY and TOGETHER_API_KEY in texto:
        texto = texto.replace(TOGETHER_API_KEY, "***")
    return texto


class MotorLLM:
    """Envuelve al cliente del proveedor y traduce sus respuestas al formato interno."""

    def __init__(self, modelo: str = MODELO_LLM_PREDETERMINADO, cliente=None) -> None:
        self.modelo = modelo
        # Muestreo como ATRIBUTOS de la instancia, no solo como argumentos de la
        # llamada (T-14). Los sliders de la GUI los mueven en vivo, y el orquestador
        # llama a `responder()` sin pasarlos: si vivieran solo en la firma, mover un
        # slider no habria cambiado nada y el control seria decorativo.
        self.temperatura = TEMPERATURA_PREDETERMINADA
        self.top_p = TOP_P_PREDETERMINADO
        self._cliente = cliente or openai.OpenAI(
            api_key=TOGETHER_API_KEY,
            base_url=TOGETHER_BASE_URL,
            timeout=TIMEOUT_SEGUNDOS,
        )

    def cambiar_modelo(self, modelo: str) -> None:
        """Cambia el modelo sin reiniciar: el cliente y la conversacion siguen vivos."""
        if not modelo or not modelo.strip():
            raise ValueError("El identificador del modelo no puede estar vacio.")
        self.modelo = modelo

    def responder(self, mensajes: list[dict],
                  temperatura: float | None = None,
                  top_p: float | None = None,
                  herramientas: list[dict] | None = None) -> RespuestaDelModelo:
        """Pide una respuesta al modelo con el historial completo.

        `mensajes` viene de `core/memory.py` y ya trae el system prompt. Este modulo
        no lo agrega por su cuenta para no terminar con dos mensajes de sistema
        contradictorios.

        Si no se pasan `temperatura` ni `top_p` se usan los de la instancia, que es lo
        que mueven los sliders. Pasarlos explicitamente sigue funcionando y tiene
        prioridad: las pruebas lo aprovechan para fijar valores sin tocar el objeto.
        """
        peticion = {
            "model": self.modelo,
            "messages": mensajes,
            "temperature": self.temperatura if temperatura is None else temperatura,
            "top_p": self.top_p if top_p is None else top_p,
        }
        # Solo se envia el campo de herramientas si de verdad hay alguna: mandar una
        # lista vacia hace que algunos proveedores rechacen la peticion.
        if herramientas:
            peticion["tools"] = herramientas
            peticion["tool_choice"] = "auto"

        try:
            respuesta = self._cliente.chat.completions.create(**peticion)
        except openai.APITimeoutError as excepcion:
            raise ModeloDemasiadoLento(
                "El modelo esta tardando demasiado en contestar. Si moviste la "
                "temperatura muy arriba, bajala un poco y vuelve a intentarlo."
            ) from excepcion
        except openai.APIConnectionError as excepcion:
            raise SinConexionLLM(
                "No se pudo contactar al modelo. Revisa tu conexion a internet e "
                "intenta de nuevo."
            ) from excepcion
        except (openai.AuthenticationError, openai.PermissionDeniedError) as excepcion:
            raise CredencialRechazadaLLM(
                "El servicio rechazo las credenciales. Verifica que TOGETHER_API_KEY "
                "en el archivo .env sea correcta y que la cuenta tenga saldo."
            ) from excepcion
        except openai.RateLimitError as excepcion:
            raise CredencialRechazadaLLM(
                "El servicio esta limitando las peticiones o la cuenta se quedo sin "
                "saldo. Espera un momento y vuelve a intentar."
            ) from excepcion
        except openai.APIStatusError as excepcion:
            raise RespuestaInvalida(
                f"El modelo respondio con un error (codigo {excepcion.status_code}). "
                "Intenta de nuevo en un momento."
            ) from excepcion
        except Exception as excepcion:  # noqa: BLE001
            raise RespuestaInvalida(
                "Ocurrio un problema inesperado al consultar al modelo: "
                + _sin_credenciales(str(excepcion))
            ) from excepcion

        return interpretar_respuesta(respuesta)


# --- Interpretacion de la respuesta ----------------------------------------
# Se deja como funcion suelta, fuera de la clase, para poder probarla con datos
# fijos sin red, sin credenciales y sin construir un cliente. Es el gate de T-07.

def interpretar_respuesta(respuesta) -> RespuestaDelModelo:
    """Traduce la respuesta cruda de la API al formato interno del proyecto.

    Es tolerante a proposito: una respuesta rara del modelo no debe tumbar la
    aplicacion a mitad de la demostracion. Solo se levanta excepcion cuando no hay
    absolutamente nada aprovechable.
    """
    opciones = _atributo(respuesta, "choices") or []
    if not opciones:
        raise RespuestaInvalida(
            "El modelo devolvio una respuesta sin contenido. Intenta de nuevo."
        )

    mensaje = _atributo(opciones[0], "message")
    if mensaje is None:
        raise RespuestaInvalida(
            "El modelo devolvio una respuesta con un formato que no se pudo leer."
        )

    texto = _atributo(mensaje, "content") or ""
    resultado = RespuestaDelModelo(
        texto=texto.strip(),
        mensaje_crudo=_a_diccionario(mensaje),
    )

    for llamada in _atributo(mensaje, "tool_calls") or []:
        funcion = _atributo(llamada, "function")
        nombre = _atributo(funcion, "name") or ""
        crudos = _atributo(funcion, "arguments")

        try:
            argumentos = _argumentos_a_diccionario(crudos)
        except ValueError:
            # JSON malformado: se descarta ESA herramienta y se sigue adelante con el
            # texto disponible (seccion 13 del diseno). No se reintenta ni se rompe
            # el turno; una herramienta perdida es mejor que una demo caida.
            resultado.tools_descartadas.append(nombre or "desconocida")
            continue

        resultado.peticiones_de_tool.append(
            PeticionDeTool(
                id=_atributo(llamada, "id") or "",
                nombre=nombre,
                argumentos=argumentos,
            )
        )

    return resultado


def _argumentos_a_diccionario(crudos) -> dict:
    """Los argumentos llegan como texto JSON; a veces ya como diccionario."""
    if crudos is None or crudos == "":
        return {}
    if isinstance(crudos, dict):
        return crudos
    datos = json.loads(crudos)  # ValueError si viene malformado
    if not isinstance(datos, dict):
        raise ValueError("Los argumentos de la herramienta no son un objeto JSON.")
    return datos


def _atributo(objeto, nombre):
    """Lee un campo tanto de un objeto del SDK como de un diccionario.

    El SDK devuelve objetos con atributos, pero las pruebas y algunos proveedores
    entregan diccionarios. Aceptar ambos evita duplicar la logica de interpretacion.
    """
    if objeto is None:
        return None
    if isinstance(objeto, dict):
        return objeto.get(nombre)
    return getattr(objeto, nombre, None)


def _a_diccionario(mensaje) -> dict:
    """Convierte el mensaje del asistente a diccionario para guardarlo en memoria."""
    if isinstance(mensaje, dict):
        return mensaje
    for metodo in ("model_dump", "to_dict", "dict"):
        conversor = getattr(mensaje, metodo, None)
        if callable(conversor):
            try:
                return conversor()
            except Exception:  # noqa: BLE001 - se intenta el siguiente conversor
                continue
    return {"role": "assistant", "content": _atributo(mensaje, "content") or ""}
