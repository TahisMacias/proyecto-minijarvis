"""Pruebas de las herramientas de Tool Calling (gate de T-15).

Nada de esto sale a la red, abre un navegador ni gasta saldo. Lo que se verifica es lo
que puede hacer dano: que la calculadora no ejecute nada que no sea aritmetica, y que
`abrir_kiosk` no lance un proceso hacia un sitio que no este en la lista blanca.

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
    abrir_kiosk,
    buscar_web,
    calcular,
    construir_comando,
    ejecutar_herramienta,
    estado_laptop,
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
# abrir_kiosk - la lista blanca, sin lanzar ningun proceso
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
    comando = construir_comando("https://google.com/buscar?q=a&b=c")
    kiosk = [parte for parte in comando if parte.startswith("--kiosk=")]
    assert len(kiosk) == 1
    assert kiosk[0] == "--kiosk=https://google.com/buscar?q=a&b=c"


def test_un_sitio_prohibido_no_lanza_ningun_proceso():
    """La comprobacion que de verdad importa: se valida ANTES de construir y lanzar."""
    lanzamientos = []
    respuesta = abrir_kiosk("https://banco-falso.com", lanzar=lanzamientos.append)
    assert lanzamientos == [], "se intento lanzar un proceso hacia un sitio prohibido"
    assert "no esta en la lista" in respuesta


def test_un_sitio_permitido_si_lanza_el_comando_correcto():
    lanzamientos = []
    respuesta = abrir_kiosk("https://es.wikipedia.org/wiki/Transformer",
                            lanzar=lanzamientos.append)
    assert len(lanzamientos) == 1
    assert lanzamientos[0][1] == "--kiosk=https://es.wikipedia.org/wiki/Transformer"
    assert "Listo" in respuesta


def test_si_falta_el_navegador_se_explica_sin_reventar():
    def lanzar_que_falla(_comando):
        raise FileNotFoundError("no existe msedge.exe")

    respuesta = abrir_kiosk("https://google.com", lanzar=lanzar_que_falla)
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
    assert "no devolvio ningun resultado" in respuesta


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


def test_las_cuatro_herramientas_del_plan_estan_declaradas():
    assert NOMBRES_DECLARADOS == {
        "calcular", "estado_laptop", "buscar_web", "abrir_kiosk"
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
