"""Pruebas de las herramientas de Tool Calling (gate de T-15).

Nada de esto sale a la red, abre un navegador ni gasta saldo. Lo que se verifica es lo
que puede hacer dano: que la calculadora no ejecute nada que no sea aritmetica, y que
`abrir_pagina` no lance un proceso hacia un sitio que no este en la lista blanca.

La prueba mas importante del archivo es `test_no_hay_eval_ni_exec_en_el_codigo`: no
comprueba un comportamiento, comprueba una PROHIBICION. Las demas dicen que hoy la
calculadora rechaza lo que se le ocurrio a quien la escribio; esa dice que manana nadie
podra colar un atajo con eval, aunque no se le ocurra el caso concreto.
"""

import ast
import json
from pathlib import Path

import pytest

from tools.manifest import MANIFIESTO, NOMBRES_DECLARADOS
from tools.system_skills import (
    UrlNoPermitida,
    abrir_pagina,
    buscar_web,
    calcular,
    clima,
    construir_comando,
    ejecutar_herramienta,
    estado_laptop,
    hora,
    validar_url,
)


RAIZ = Path(__file__).resolve().parents[1]


# ===========================================================================
# La prohibicion: nada de eval, exec ni compile en todo tools/
# ===========================================================================

def test_no_hay_eval_ni_exec_en_el_codigo():
    """El criterio de T-15 no es negociable: nada de eval sobre lo que diga el modelo.

    Se lee el arbol de sintaxis de cada archivo de tools/ y se busca cualquier llamada
    a eval, exec o compile. Si alguien las anade en el futuro, esta prueba se pone roja
    antes de que llegue a un repositorio publico.
    """
    prohibidas = {"eval", "exec", "compile", "__import__"}
    encontradas = []

    for archivo in sorted((RAIZ / "tools").glob("*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                if nodo.func.id in prohibidas:
                    encontradas.append(f"{archivo.name}:{nodo.lineno} -> {nodo.func.id}")

    assert not encontradas, (
        "se encontraron llamadas prohibidas en tools/: " + ", ".join(encontradas)
    )


# ===========================================================================
# calcular - lo que debe resolver
# ===========================================================================

def test_resuelve_la_pregunta_que_el_modelo_no_supo():
    """El caso real que origino esta herramienta: la raiz cuadrada de 3340."""
    resultado = calcular("3340 ** 0.5")
    assert "57.7927" in resultado


def test_sqrt_y_potencia_dan_lo_mismo():
    assert calcular("sqrt(3340)")[-12:] == calcular("3340 ** 0.5")[-12:]


@pytest.mark.parametrize("expresion,esperado", [
    ("2 + 2", "4"),
    ("(2400 / 12) * 3", "600"),
    ("10 // 3", "3"),
    ("10 % 3", "1"),
    ("-5 + 8", "3"),
    ("factorial(5)", "120"),
    ("max(3, 9, 2)", "9"),
    ("round(2.567, 1)", "2.6"),
    ("abs(-42)", "42"),
])
def test_operaciones_correctas(expresion, esperado):
    assert esperado in calcular(expresion)


def test_un_entero_no_se_lee_como_decimal():
    """Si el resultado es redondo, la voz debe decir 600 y no 600.0."""
    assert "600.0" not in calcular("(2400 / 12) * 3")


def test_un_decimal_largo_se_marca_como_aproximado():
    """No se puede llamar exacto a un numero que se acaba de redondear."""
    assert "aproximadamente" in calcular("1 / 3")


def test_las_constantes_conocidas_funcionan():
    assert "3.14159" in calcular("pi")


# ===========================================================================
# calcular - lo que debe rechazar
# ===========================================================================

@pytest.mark.parametrize("ataque", [
    '__import__("os").system("calc")',
    "().__class__.__bases__",
    "open('secreto.txt')",
    "globals()",
    "[1, 2, 3]",
    "'texto'",
    "lambda: 1",
    "x = 5",
    "print(1)",
])
def test_rechaza_lo_que_no_es_aritmetica(ataque):
    """Ninguna de estas debe ejecutarse. Todas deben salir como frase explicativa."""
    resultado = calcular(ataque)
    assert "No puedo calcular eso" in resultado or "No pude entender" in resultado


def test_el_rechazo_no_levanta_excepcion():
    """Una herramienta que revienta corta el turno. Esta siempre devuelve texto."""
    for entrada in ["", "   ", None, 12345, "))))"]:
        assert isinstance(calcular(entrada), str)


def test_un_exponente_gigante_no_cuelga_la_aplicacion():
    """Aritmetica legitima que agotaria la memoria. Corre en el hilo del turno."""
    assert "demasiado grande" in calcular("2 ** 10 ** 9")


def test_division_entre_cero_se_explica():
    assert "dividir entre cero" in calcular("10 / 0")


def test_una_expresion_larguisima_se_rechaza_por_tamano():
    assert "demasiado larga" in calcular("1+" * 400 + "1")


# ===========================================================================
# abrir_pagina - la lista blanca, sin lanzar ningun proceso
# ===========================================================================

@pytest.mark.parametrize("url", [
    "https://es.wikipedia.org/wiki/Transformer",
    "https://www.youtube.com/watch?v=algo",
    "https://github.com/TahisMacias/proyecto-minijarvis",
    "https://google.com",
])
def test_los_dominios_permitidos_pasan(url):
    assert validar_url(url) == url


@pytest.mark.parametrize("url,motivo", [
    ("https://youtube.com.sitio-ajeno.ru/x", "un dominio que solo PARECE youtube"),
    ("https://banco-falso.com", "un dominio cualquiera"),
    ("file:///C:/Windows/System32", "un esquema que no es http"),
    ("javascript:alert(1)", "un esquema ejecutable"),
    ("", "vacio"),
    ("no es una url", "texto suelto"),
])
def test_los_dominios_no_permitidos_se_rechazan(url, motivo):
    with pytest.raises(UrlNoPermitida):
        validar_url(url)


def test_el_dominio_se_valida_por_hostname_y_no_por_texto():
    """La trampa clasica: buscar youtube.com DENTRO de la cadena de la url.

    `https://youtube.com.sitio-ajeno.ru` contiene el texto "youtube.com" y sin embargo
    pertenece a otro dueno por completo. Solo mirar el hostname real lo detecta.
    """
    assert "youtube.com" in "https://youtube.com.sitio-ajeno.ru/x"
    with pytest.raises(UrlNoPermitida):
        validar_url("https://youtube.com.sitio-ajeno.ru/x")


def test_el_comando_es_una_lista_de_argumentos():
    """Nunca una cadena: es lo que impide que la url se interprete como ordenes."""
    comando = construir_comando("https://google.com")
    assert isinstance(comando, list)
    assert all(isinstance(parte, str) for parte in comando)


def test_la_url_viaja_en_un_solo_argumento():
    """Aunque llevara espacios o simbolos, sigue siendo UN argumento, no varios."""
    url = "https://google.com/buscar?q=a&b=c"
    comando = construir_comando(url)
    assert comando.count(url) == 1


def test_la_url_va_suelta_y_no_pegada_al_interruptor():
    """Defecto real que la duena encontro el 2026-08-23: pidio Wikipedia y salio Edge
    con su pagina de importar datos.

    En Chromium `--kiosk` es un INTERRUPTOR, no una opcion con valor. Escribir
    `--new-window=https://...` no da error: el navegador ignora la direccion y arranca con
    su pagina de inicio. El comando estaba bien formado y aun asi hacia lo que no era.

    Por eso esta prueba comprueba la POSICION y no solo la presencia: la direccion
    tiene que ser el argumento inmediatamente siguiente a `--kiosk`.
    """
    url = "https://es.wikipedia.org/wiki/Transformer"
    comando = construir_comando(url)

    assert "--new-window" in comando, "falta el interruptor --kiosk"
    assert not any(parte.startswith("--new-window=") for parte in comando), (
        "la direccion esta pegada a --kiosk con un igual; Edge la ignora"
    )
    assert comando[comando.index("--new-window") + 1] == url, (
        "la direccion debe ir justo despues de --kiosk"
    )


def test_un_sitio_prohibido_no_lanza_ningun_proceso():
    """La comprobacion que de verdad importa: se valida ANTES de construir y lanzar."""
    lanzamientos = []
    respuesta = abrir_pagina("https://banco-falso.com", lanzar=lanzamientos.append)
    assert lanzamientos == [], "se intento lanzar un proceso hacia un sitio prohibido"
    assert "no esta en la lista" in respuesta


def test_un_sitio_permitido_si_lanza_el_comando_correcto():
    url = "https://es.wikipedia.org/wiki/Transformer"
    lanzamientos = []
    respuesta = abrir_pagina(url, lanzar=lanzamientos.append)

    assert len(lanzamientos) == 1
    comando = lanzamientos[0]
    # La direccion, suelta y justo detras del interruptor. Ver
    # test_la_url_va_suelta_y_no_pegada_a_kiosk para el porque.
    assert comando[comando.index("--new-window") + 1] == url
    assert "Listo" in respuesta


def test_si_falta_el_navegador_se_explica_sin_reventar():
    def lanzar_que_falla(_comando):
        raise FileNotFoundError("no existe msedge.exe")

    respuesta = abrir_pagina("https://google.com", lanzar=lanzar_que_falla)
    assert "No encontre Microsoft Edge" in respuesta


# ===========================================================================
# buscar_web - con buscador inyectado, sin salir a la red
# ===========================================================================

def test_la_busqueda_resume_los_resultados():
    def buscador_falso(consulta, max_results):
        return [{"title": "Transformer", "body": "Una arquitectura de red neuronal."}]

    respuesta = buscar_web("que es un transformer", buscador=buscador_falso)
    assert "Transformer" in respuesta
    assert "arquitectura de red neuronal" in respuesta


def test_una_busqueda_sin_resultados_se_dice_con_palabras():
    respuesta = buscar_web("algo rarisimo", buscador=lambda c, max_results: [])
    assert "No pude completar la busqueda" in respuesta


def test_una_busqueda_vacia_se_reintenta_una_vez():
    """Defecto real del 2026-08-23: la libreria anterior devolvia cero resultados de
    forma intermitente para la MISMA consulta, sin lanzar error. El modelo recibia una
    busqueda vacia y contestaba que no tenia acceso a internet.

    Se migro a `ddgs`, que resulto estable, y ademas se reintenta una vez: un buscador
    publico y gratuito puede tener un mal momento, y esto se demuestra en vivo.
    """
    intentos = []

    def a_la_segunda(consulta, max_results):
        intentos.append(consulta)
        return [] if len(intentos) == 1 else [{"title": "T", "body": "cuerpo"}]

    respuesta = buscar_web("lo que sea", buscador=a_la_segunda)
    assert len(intentos) == 2, "no reintento"
    assert "cuerpo" in respuesta, "descarto el resultado del segundo intento"


def test_no_se_reintenta_si_el_primer_intento_ya_trajo_algo():
    """Reintentar cuando no hace falta seria pagar un segundo viaje a la red por nada."""
    intentos = []

    def siempre_bien(consulta, max_results):
        intentos.append(consulta)
        return [{"title": "T", "body": "cuerpo"}]

    buscar_web("x", buscador=siempre_bien)
    assert len(intentos) == 1


def test_si_el_buscador_falla_no_se_rompe_el_turno():
    def buscador_roto(consulta, max_results):
        raise ConnectionError("sin red")

    respuesta = buscar_web("lo que sea", buscador=buscador_roto)
    assert "No pude completar la busqueda" in respuesta


def test_un_resumen_larguisimo_se_recorta():
    def buscador_verboso(consulta, max_results):
        return [{"title": "T", "body": "palabra " * 500}]

    respuesta = buscar_web("x", buscador=buscador_verboso)
    assert "..." in respuesta
    assert len(respuesta) < 600


# ===========================================================================
# estado_laptop
# ===========================================================================

def test_el_estado_de_la_laptop_devuelve_una_frase():
    respuesta = estado_laptop()
    assert isinstance(respuesta, str) and respuesta.endswith(".")


# ===========================================================================
# Coherencia entre lo que se declara y lo que existe
# ===========================================================================

def test_el_manifiesto_es_json_valido():
    """Viaja a la API tal cual: si no serializa, la peticion entera falla."""
    assert json.dumps(MANIFIESTO)


def test_cada_herramienta_declarada_tiene_implementacion():
    """Declarar una herramienta que no existe hace que el modelo la pida y falle."""
    for nombre in NOMBRES_DECLARADOS:
        peticion = type("P", (), {"nombre": nombre, "argumentos": {}})()
        assert "no existe" not in ejecutar_herramienta(peticion), (
            f"{nombre} esta en el manifiesto pero no tiene implementacion"
        )


def test_las_seis_herramientas_estan_declaradas():
    """`clima` y `hora` se anadieron al releer la seccion 5.2 del enunciado, que las
    nombra las dos en su lista de funciones reales."""
    assert NOMBRES_DECLARADOS == {
        "calcular", "clima", "hora", "estado_laptop", "buscar_web", "abrir_pagina"
    }


def test_cada_entrada_del_manifiesto_tiene_la_forma_que_pide_la_api():
    for entrada in MANIFIESTO:
        assert entrada["type"] == "function"
        funcion = entrada["function"]
        assert funcion["name"] and funcion["description"]
        assert funcion["parameters"]["type"] == "object"
        for requerido in funcion["parameters"].get("required", []):
            assert requerido in funcion["parameters"]["properties"], (
                f"{funcion['name']} exige {requerido} pero no lo describe"
            )


# ===========================================================================
# El despachador
# ===========================================================================

def test_una_herramienta_inventada_por_el_modelo_no_rompe_nada():
    """Los modelos inventan nombres. Debe contestarse, no reventar."""
    peticion = type("P", (), {"nombre": "borrar_todo", "argumentos": {}})()
    assert "no existe" in ejecutar_herramienta(peticion)


def test_el_despachador_pasa_los_argumentos():
    peticion = type("P", (), {"nombre": "calcular",
                              "argumentos": {"expresion": "7 * 6"}})()
    assert "42" in ejecutar_herramienta(peticion)


def test_argumentos_de_forma_inesperada_no_tumban_el_despachador():
    for argumentos in [None, "texto suelto", 42, []]:
        peticion = type("P", (), {"nombre": "calcular", "argumentos": argumentos})()
        assert isinstance(ejecutar_herramienta(peticion), str)


# ===========================================================================
# clima - con el servicio inyectado, sin salir a internet
# ===========================================================================

def _servicio_falso(geo=None, tiempo=None, fallar_en=None):
    """Devuelve una funcion `pedir` que imita a open-meteo sin tocar la red."""
    def pedir(url, parametros):
        if fallar_en and fallar_en in url:
            raise ConnectionError("sin red")
        if "geocoding" in url:
            return geo if geo is not None else {
                "results": [{"name": "Guayaquil", "country": "Ecuador",
                             "latitude": -2.19, "longitude": -79.89}]
            }
        return tiempo if tiempo is not None else {
            "current": {"temperature_2m": 28.1, "apparent_temperature": 31.4,
                        "relative_humidity_2m": 64, "weather_code": 1}
        }
    return pedir


def test_el_clima_se_dice_en_una_frase_hablable():
    respuesta = clima("Guayaquil", pedir=_servicio_falso())
    assert "Guayaquil" in respuesta
    assert "28 grados" in respuesta
    assert "64 por ciento" in respuesta
    # Nada de simbolos que no se puedan pronunciar.
    for simbolo in ("°", "%", "{", "[", "|"):
        assert simbolo not in respuesta


def test_el_codigo_del_cielo_se_traduce_a_palabras():
    """El servicio devuelve un numero. Un numero no se puede leer en voz alta."""
    respuesta = clima("X", pedir=_servicio_falso())
    assert "casi despejado" in respuesta
    assert "1" not in respuesta.split("grados")[0].replace("28", "")


def test_la_sensacion_termica_solo_se_menciona_si_difiere():
    """Repetir el mismo numero dos veces en voz alta suena a error del asistente."""
    igual = _servicio_falso(tiempo={"current": {
        "temperature_2m": 20.0, "apparent_temperature": 20.2,
        "relative_humidity_2m": 50, "weather_code": 0}})
    assert "se sienten como" not in clima("X", pedir=igual)

    distinta = _servicio_falso(tiempo={"current": {
        "temperature_2m": 28.0, "apparent_temperature": 34.0,
        "relative_humidity_2m": 80, "weather_code": 0}})
    assert "se sienten como 34" in clima("X", pedir=distinta)


def test_una_ciudad_que_no_existe_se_explica_con_palabras():
    vacio = _servicio_falso(geo={"results": []})
    respuesta = clima("Ciudadinventada", pedir=vacio)
    assert "No encontre" in respuesta
    assert "Ciudadinventada" in respuesta


def test_sin_red_el_clima_no_rompe_el_turno():
    respuesta = clima("Quito", pedir=_servicio_falso(fallar_en="geocoding"))
    assert "conexion a internet" in respuesta


def test_si_falla_solo_la_segunda_llamada_tambien_se_explica():
    respuesta = clima("Quito", pedir=_servicio_falso(fallar_en="forecast"))
    assert "no pude leer el clima" in respuesta.lower()


def test_sin_ciudad_se_pide_la_ciudad():
    for entrada in ["", "   ", None, 42]:
        assert isinstance(clima(entrada), str)
    assert "que ciudad" in clima("")


def test_el_clima_esta_enchufado_al_despachador():
    peticion = type("P", (), {"nombre": "clima", "argumentos": {"ciudad": "Guayaquil"}})()
    assert "no existe" not in ejecutar_herramienta(peticion)


# ===========================================================================
# hora - el modelo no tiene reloj
# ===========================================================================

def test_la_hora_se_dice_como_la_diria_una_persona():
    """Las 14:05 se dicen "dos y cinco de la tarde". Esto se lee EN VOZ ALTA: un
    reloj de 24 horas suena a locutor de aeropuerto."""
    from datetime import datetime
    respuesta = hora(datetime(2026, 8, 23, 14, 5))
    assert "2 y 5 de la tarde" in respuesta
    assert "14" not in respuesta


@pytest.mark.parametrize("h,m,esperado", [
    (0, 30, "12 y media de la madrugada"),
    (9, 15, "9 y cuarto de la manana"),
    (14, 0, "2 en punto de la tarde"),
    (21, 47, "9 y 47 de la noche"),
    (12, 0, "12 en punto de la tarde"),
])
def test_las_franjas_del_dia_y_las_medias(h, m, esperado):
    from datetime import datetime
    assert esperado in hora(datetime(2026, 8, 23, h, m))


def test_la_fecha_va_en_palabras_y_completa():
    from datetime import datetime
    respuesta = hora(datetime(2026, 8, 23, 10, 0))
    assert "domingo 23 de agosto de 2026" in respuesta


def test_la_hora_esta_enchufada_al_despachador():
    peticion = type("P", (), {"nombre": "hora", "argumentos": {}})()
    assert "no existe" not in ejecutar_herramienta(peticion)
