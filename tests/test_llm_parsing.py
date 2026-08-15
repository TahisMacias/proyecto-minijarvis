"""Pruebas de interpretacion de respuestas del LLM (tarea T-07).

Corren con datos fijos: ni red, ni credenciales, ni un centavo de saldo. Lo que se
prueba no es que el modelo conteste bien —eso no es determinista y no se puede
verificar en un gate— sino que ESTE codigo entienda correctamente cualquier forma en
que la respuesta pueda llegar, incluidas las formas rotas.

El caso mas importante es el del JSON malformado en los argumentos de una
herramienta: la seccion 13 del diseno exige que ahi se ignore la herramienta y se
responda con el texto disponible, en vez de tumbar el turno.
"""

import pytest

from core.llm_engine import (
    RespuestaInvalida,
    interpretar_respuesta,
)


def _respuesta(content=None, tool_calls=None):
    """Arma una respuesta con la misma forma que devuelve la API, en diccionarios."""
    mensaje = {"role": "assistant", "content": content}
    if tool_calls is not None:
        mensaje["tool_calls"] = tool_calls
    return {"choices": [{"message": mensaje}]}


def _llamada(nombre, argumentos, identificador="call-1"):
    return {
        "id": identificador,
        "type": "function",
        "function": {"name": nombre, "arguments": argumentos},
    }


# --- Respuesta de solo texto -----------------------------------------------

def test_respuesta_de_texto_simple():
    resultado = interpretar_respuesta(_respuesta(content="Hola, soy Mini-JARVIS."))

    assert resultado.texto == "Hola, soy Mini-JARVIS."
    assert resultado.peticiones_de_tool == []
    assert not resultado.pide_herramienta


def test_el_texto_llega_sin_espacios_sobrantes():
    resultado = interpretar_respuesta(_respuesta(content="  Hola.\n\n"))
    assert resultado.texto == "Hola."


def test_content_nulo_no_rompe_nada():
    """Cuando el modelo solo pide herramientas, `content` llega como None."""
    resultado = interpretar_respuesta(_respuesta(content=None))
    assert resultado.texto == ""


# --- Peticiones de herramienta ---------------------------------------------

def test_peticion_de_herramienta_bien_formada():
    resultado = interpretar_respuesta(
        _respuesta(content=None, tool_calls=[_llamada("estado_laptop", "{}")])
    )

    assert resultado.pide_herramienta
    assert len(resultado.peticiones_de_tool) == 1
    peticion = resultado.peticiones_de_tool[0]
    assert peticion.nombre == "estado_laptop"
    assert peticion.argumentos == {}
    assert peticion.id == "call-1"


def test_los_argumentos_json_se_convierten_a_diccionario():
    resultado = interpretar_respuesta(
        _respuesta(tool_calls=[_llamada("buscar_web", '{"consulta": "clima en Quito"}')])
    )

    assert resultado.peticiones_de_tool[0].argumentos == {"consulta": "clima en Quito"}


def test_varias_herramientas_en_un_mismo_turno():
    resultado = interpretar_respuesta(
        _respuesta(
            tool_calls=[
                _llamada("estado_laptop", "{}", "call-1"),
                _llamada("buscar_web", '{"consulta": "hora"}', "call-2"),
            ]
        )
    )

    assert [p.nombre for p in resultado.peticiones_de_tool] == [
        "estado_laptop",
        "buscar_web",
    ]
    assert [p.id for p in resultado.peticiones_de_tool] == ["call-1", "call-2"]


def test_texto_y_herramienta_conviven():
    """El modelo puede avisar en voz alta mientras pide una herramienta."""
    resultado = interpretar_respuesta(
        _respuesta(content="Dejame revisar.", tool_calls=[_llamada("estado_laptop", "{}")])
    )

    assert resultado.texto == "Dejame revisar."
    assert resultado.pide_herramienta


# --- JSON malformado: el caso que exige la seccion 13 del diseno ------------

def test_json_malformado_descarta_la_herramienta_y_conserva_el_texto():
    resultado = interpretar_respuesta(
        _respuesta(
            content="Te reviso la bateria.",
            tool_calls=[_llamada("estado_laptop", "{esto no es json")],
        )
    )

    assert resultado.texto == "Te reviso la bateria."
    assert resultado.peticiones_de_tool == []
    assert resultado.tools_descartadas == ["estado_laptop"]


def test_una_herramienta_rota_no_arrastra_a_las_demas():
    resultado = interpretar_respuesta(
        _respuesta(
            tool_calls=[
                _llamada("estado_laptop", "{roto", "call-1"),
                _llamada("buscar_web", '{"consulta": "hora"}', "call-2"),
            ]
        )
    )

    assert [p.nombre for p in resultado.peticiones_de_tool] == ["buscar_web"]
    assert resultado.tools_descartadas == ["estado_laptop"]


def test_argumentos_que_no_son_un_objeto_tambien_se_descartan():
    """Una lista o un numero no sirven como argumentos con nombre."""
    resultado = interpretar_respuesta(
        _respuesta(tool_calls=[_llamada("buscar_web", "[1, 2, 3]")])
    )

    assert resultado.peticiones_de_tool == []
    assert resultado.tools_descartadas == ["buscar_web"]


def test_argumentos_vacios_equivalen_a_sin_argumentos():
    resultado = interpretar_respuesta(
        _respuesta(tool_calls=[_llamada("estado_laptop", "")])
    )

    assert resultado.peticiones_de_tool[0].argumentos == {}
    assert resultado.tools_descartadas == []


# --- Respuestas inservibles -------------------------------------------------

def test_respuesta_sin_opciones_levanta_error_tipado():
    with pytest.raises(RespuestaInvalida):
        interpretar_respuesta({"choices": []})


def test_respuesta_sin_mensaje_levanta_error_tipado():
    with pytest.raises(RespuestaInvalida):
        interpretar_respuesta({"choices": [{}]})


# --- Formato de objeto, no de diccionario -----------------------------------

def test_tambien_entiende_los_objetos_del_sdk():
    """El SDK devuelve objetos con atributos; las pruebas usan diccionarios.

    Ambos caminos deben dar el mismo resultado, porque en produccion llega el
    primero y en el gate se verifica el segundo.
    """
    class Funcion:
        name = "buscar_web"
        arguments = '{"consulta": "noticias"}'

    class Llamada:
        id = "call-9"
        function = Funcion()

    class Mensaje:
        role = "assistant"
        content = "Busco eso."
        tool_calls = [Llamada()]

    class Opcion:
        message = Mensaje()

    class Respuesta:
        choices = [Opcion()]

    resultado = interpretar_respuesta(Respuesta())

    assert resultado.texto == "Busco eso."
    assert resultado.peticiones_de_tool[0].nombre == "buscar_web"
    assert resultado.peticiones_de_tool[0].argumentos == {"consulta": "noticias"}
    assert resultado.peticiones_de_tool[0].id == "call-9"


def test_el_mensaje_crudo_se_conserva_para_el_historial():
    """La API exige que un mensaje de rol tool venga precedido por el del asistente."""
    resultado = interpretar_respuesta(
        _respuesta(content="ok", tool_calls=[_llamada("estado_laptop", "{}")])
    )

    assert resultado.mensaje_crudo is not None
    assert resultado.mensaje_crudo["role"] == "assistant"
    assert "tool_calls" in resultado.mensaje_crudo
