"""Pruebas de la memoria conversacional (tarea T-04).

Estas pruebas corren sin red, sin microfono y sin ninguna llamada a la API: la
memoria es la pieza del proyecto que se puede verificar entera de forma
determinista, y por eso se construyo temprano.

Los cuatro casos que exige el plan son de frontera: memoria vacia, por debajo del
limite, justo en el limite y por encima. El punto interesante siempre esta en el
borde: un error tipico de este tipo de codigo es descartar un turno de mas (o de
menos) exactamente cuando se alcanza el limite.
"""

import pytest

from core.memory import MemoriaConversacional


SYSTEM_DE_PRUEBA = "Eres un asistente de prueba."


def _memoria(max_turnos=3):
    return MemoriaConversacional(system_prompt=SYSTEM_DE_PRUEBA, max_turnos=max_turnos)


def _cargar_turnos(memoria, cantidad, desde=1):
    """Anade `cantidad` turnos completos numerados, para poder identificarlos luego."""
    for numero in range(desde, desde + cantidad):
        memoria.agregar_usuario(f"pregunta {numero}")
        memoria.agregar_asistente(f"respuesta {numero}")


# --- Caso 1: memoria vacia -------------------------------------------------

def test_memoria_vacia_solo_tiene_el_system_prompt():
    memoria = _memoria()
    mensajes = memoria.mensajes()

    assert memoria.numero_de_turnos() == 0
    assert len(mensajes) == 1
    assert mensajes[0] == {"role": "system", "content": SYSTEM_DE_PRUEBA}


def test_memoria_vacia_no_acepta_una_respuesta_sin_pregunta():
    """Un historial que empieza por el asistente es incoherente para el modelo."""
    memoria = _memoria()
    with pytest.raises(ValueError):
        memoria.agregar_asistente("respuesta huerfana")


# --- Caso 2: por debajo del limite -----------------------------------------

def test_por_debajo_del_limite_no_descarta_nada():
    memoria = _memoria(max_turnos=3)
    _cargar_turnos(memoria, 2)

    mensajes = memoria.mensajes()

    assert memoria.numero_de_turnos() == 2
    assert not memoria.esta_llena()
    # 1 system + 2 turnos de 2 mensajes cada uno.
    assert len(mensajes) == 5
    assert mensajes[1]["content"] == "pregunta 1"
    assert mensajes[-1]["content"] == "respuesta 2"


# --- Caso 3: justo en el limite --------------------------------------------

def test_justo_en_el_limite_conserva_todos_los_turnos():
    memoria = _memoria(max_turnos=3)
    _cargar_turnos(memoria, 3)

    contenidos = [m["content"] for m in memoria.mensajes()]

    assert memoria.numero_de_turnos() == 3
    assert memoria.esta_llena()
    assert "pregunta 1" in contenidos, "en el limite exacto todavia no se descarta nada"
    assert "respuesta 3" in contenidos


# --- Caso 4: por encima del limite -----------------------------------------

def test_por_encima_del_limite_descarta_el_turno_mas_antiguo():
    memoria = _memoria(max_turnos=3)
    _cargar_turnos(memoria, 5)

    contenidos = [m["content"] for m in memoria.mensajes()]

    assert memoria.numero_de_turnos() == 3
    assert "pregunta 1" not in contenidos
    assert "pregunta 2" not in contenidos
    # Se conservan los tres mas recientes, no los tres primeros.
    assert "pregunta 3" in contenidos
    assert "pregunta 5" in contenidos
    assert "respuesta 5" in contenidos


def test_el_system_prompt_nunca_se_descarta():
    """Es la invariante mas importante: sin el, el asistente pierde su identidad."""
    memoria = _memoria(max_turnos=2)
    _cargar_turnos(memoria, 30)

    mensajes = memoria.mensajes()

    assert mensajes[0]["role"] == "system"
    assert mensajes[0]["content"] == SYSTEM_DE_PRUEBA
    assert memoria.numero_de_turnos() == 2


def test_el_descarte_no_parte_un_turno_por_la_mitad():
    """Nunca debe quedar una respuesta sin su pregunta, ni al reves."""
    memoria = _memoria(max_turnos=2)
    _cargar_turnos(memoria, 4)

    conversacion = memoria.mensajes()[1:]  # se salta el system prompt

    assert len(conversacion) % 2 == 0
    for indice in range(0, len(conversacion), 2):
        assert conversacion[indice]["role"] == "user"
        assert conversacion[indice + 1]["role"] == "assistant"


# --- Tool calling ----------------------------------------------------------

def test_los_mensajes_de_tool_viajan_dentro_de_su_turno():
    """Al descartar un turno con herramienta, se va completo: pregunta y resultado."""
    memoria = _memoria(max_turnos=1)

    memoria.agregar_usuario("como esta la bateria")
    memoria.agregar_mensaje_de_tool("llamada-1", '{"bateria": 87}')
    memoria.agregar_asistente("Tienes 87 % de bateria.")
    _cargar_turnos(memoria, 1, desde=9)

    contenidos = [m["content"] for m in memoria.mensajes()]

    assert memoria.numero_de_turnos() == 1
    assert '{"bateria": 87}' not in contenidos
    assert "como esta la bateria" not in contenidos
    assert "pregunta 9" in contenidos


# --- Indicadores para la GUI -----------------------------------------------

def test_estimar_tokens_crece_con_la_conversacion_y_nunca_es_negativo():
    memoria = _memoria(max_turnos=10)
    tokens_vacia = memoria.estimar_tokens()

    _cargar_turnos(memoria, 4)
    tokens_con_conversacion = memoria.estimar_tokens()

    assert tokens_vacia >= 0
    assert tokens_con_conversacion > tokens_vacia


def test_estimar_tokens_baja_cuando_el_truncado_descarta_turnos():
    """El indicador de la GUI debe reflejar el descarte, que es lo que se demuestra."""
    memoria = _memoria(max_turnos=2)
    _cargar_turnos(memoria, 2)
    tokens_lleno = memoria.estimar_tokens()

    memoria.agregar_usuario("x")  # abre un turno corto y expulsa uno largo
    tokens_tras_truncar = memoria.estimar_tokens()

    assert tokens_tras_truncar < tokens_lleno


def test_limpiar_borra_la_conversacion_pero_no_el_system_prompt():
    memoria = _memoria()
    _cargar_turnos(memoria, 2)

    memoria.limpiar()

    assert memoria.numero_de_turnos() == 0
    assert memoria.mensajes() == [{"role": "system", "content": SYSTEM_DE_PRUEBA}]


# --- Aislamiento del historial ---------------------------------------------

def test_modificar_lo_devuelto_no_altera_la_memoria():
    """mensajes() devuelve una copia: el truncado es la unica via de cambio."""
    memoria = _memoria()
    _cargar_turnos(memoria, 1)

    copia = memoria.mensajes()
    copia[0]["content"] = "otro system prompt"
    copia.append({"role": "user", "content": "inyectado"})

    mensajes = memoria.mensajes()
    assert mensajes[0]["content"] == SYSTEM_DE_PRUEBA
    assert all(m["content"] != "inyectado" for m in mensajes)


def test_un_limite_de_cero_turnos_se_rechaza_al_construir():
    with pytest.raises(ValueError):
        MemoriaConversacional(system_prompt=SYSTEM_DE_PRUEBA, max_turnos=0)
