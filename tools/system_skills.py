"""Implementacion de las herramientas que el modelo puede pedir (tarea T-15).

AQUI VIVE LA SUPERFICIE DE RIESGO DEL PROYECTO. Todo lo demas de Mini-JARVIS lee el
microfono o habla con una API; este archivo hace CUENTAS con texto que escribio un
modelo y ABRE UN PROCESO del sistema operativo. Dos reglas lo gobiernan:

REGLA 1 - NADA DE eval NI DE exec, NUNCA, SOBRE LO QUE DIGA EL MODELO.
    La forma perezosa de escribir `calcular` es pasarle la expresion a eval. Seria una
    puerta abierta: eval no distingue una suma de una llamada al sistema operativo.
    Aqui la expresion se analiza con el modulo `ast`, se rechaza cualquier nodo que no
    este en una lista blanca, y despues **se calcula el resultado recorriendo el arbol
    a mano**. No hay ninguna llamada a eval, exec ni compile en este archivo: se puede
    comprobar buscandolas, y hay una prueba que lo comprueba automaticamente en cada
    ejecucion de la suite.

REGLA 2 - LA URL SE VALIDA ANTES DE CONSTRUIR EL COMANDO, Y EL COMANDO ES UNA LISTA.
    Primero se comprueba el dominio contra la lista blanca de `config.py`; solo si pasa
    se arma el comando. Y se arma como LISTA de argumentos, nunca pegando cadenas: con
    shell=True y concatenacion, una direccion que llevara dentro un separador de
    comandos y otro programa ejecutaria las dos cosas. Con una lista de argumentos y
    sin shell, la direccion es solo un dato.

CONTRATO COMUN: toda herramienta devuelve **texto en espanol, ya redactado para que el
modelo lo lea en voz alta**, y ninguna levanta excepciones hacia afuera. Un fallo se
devuelve como frase explicativa: el orquestador se la pasa al modelo, que decide como
contarlo. Una herramienta que revienta cortaria el turno; una que explica, no.
"""

from __future__ import annotations

import ast
import math
import operator
import subprocess
import time
from urllib.parse import urlparse

from config import DOMINIOS_PERMITIDOS


# ===========================================================================
# calcular - un LLM predice texto, no calcula
# ===========================================================================
#
# Existe por un fallo real: la duena pregunto por la raiz cuadrada de 3340 y el modelo
# contesto que no tenia calculadora pero podia dar una respuesta aproximada. Un modelo
# de lenguaje predice la siguiente palabra; que acierte una cuenta es suerte
# estadistica. Python si calcula, y es exacto.

_OPERADORES_BINARIOS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_OPERADORES_UNARIOS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_FUNCIONES_PERMITIDAS = {
    "sqrt": math.sqrt, "abs": abs, "round": round, "min": min, "max": max,
    "pow": pow, "log": math.log, "log10": math.log10, "log2": math.log2,
    "exp": math.exp, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "floor": math.floor, "ceil": math.ceil, "factorial": math.factorial,
    "degrees": math.degrees, "radians": math.radians,
}

_CONSTANTES_PERMITIDAS = {"pi": math.pi, "e": math.e, "tau": math.tau}

# Topes contra una expresion que sea valida y aun asi bloquee la aplicacion. Elevar dos
# a la potencia de mil millones no es un ataque sofisticado: es aritmetica legitima que
# tarda una eternidad y agota la memoria. Como esto corre en el hilo del turno,
# colgarlo congela la conversacion entera.
_LARGO_MAXIMO_EXPRESION = 500
_NODOS_MAXIMOS = 100
_EXPONENTE_MAXIMO = 1000
_PROFUNDIDAD_MAXIMA = 25


class ExpresionNoPermitida(ValueError):
    """La expresion contiene algo que no esta en la lista blanca."""


def _evaluar_nodo(nodo, profundidad: int = 0):
    """Calcula el valor de un nodo del arbol, a mano y sin eval.

    Solo entiende los tipos de nodo de la lista blanca. Cualquier otra cosa -un nombre
    de variable, un acceso a atributo, una llamada a una funcion no permitida, un
    corchete- cae en el raise del final. La lista blanca decide lo que SI se permite,
    en vez de intentar enumerar lo que se prohibe, que es la unica forma de que esto
    siga siendo seguro cuando Python anada sintaxis nueva.
    """
    if profundidad > _PROFUNDIDAD_MAXIMA:
        raise ExpresionNoPermitida("La expresion esta demasiado anidada.")

    if isinstance(nodo, ast.Expression):
        return _evaluar_nodo(nodo.body, profundidad + 1)

    if isinstance(nodo, ast.Constant):
        if isinstance(nodo.value, bool) or not isinstance(nodo.value, (int, float)):
            raise ExpresionNoPermitida(
                "Solo se admiten numeros: nada de texto, listas ni valores logicos."
            )
        return nodo.value

    if isinstance(nodo, ast.Name):
        if nodo.id in _CONSTANTES_PERMITIDAS:
            return _CONSTANTES_PERMITIDAS[nodo.id]
        raise ExpresionNoPermitida(
            f"{nodo.id} no es un numero ni una constante conocida. Solo se admiten: "
            f"{', '.join(sorted(_CONSTANTES_PERMITIDAS))}."
        )

    if isinstance(nodo, ast.BinOp):
        funcion = _OPERADORES_BINARIOS.get(type(nodo.op))
        if funcion is None:
            raise ExpresionNoPermitida("Esa operacion no esta permitida.")
        izquierda = _evaluar_nodo(nodo.left, profundidad + 1)
        derecha = _evaluar_nodo(nodo.right, profundidad + 1)
        if isinstance(nodo.op, ast.Pow) and abs(derecha) > _EXPONENTE_MAXIMO:
            raise ExpresionNoPermitida(
                f"El exponente {derecha} es demasiado grande para calcularlo aqui."
            )
        return funcion(izquierda, derecha)

    if isinstance(nodo, ast.UnaryOp):
        funcion = _OPERADORES_UNARIOS.get(type(nodo.op))
        if funcion is None:
            raise ExpresionNoPermitida("Ese signo no esta permitido.")
        return funcion(_evaluar_nodo(nodo.operand, profundidad + 1))

    if isinstance(nodo, ast.Call):
        # Solo se admite la forma nombre(...). Un acceso del tipo objeto.metodo(...) es
        # un ast.Attribute y no llega hasta aqui: esa es justamente la puerta por la
        # que se colaria una llamada al sistema operativo.
        if not isinstance(nodo.func, ast.Name):
            raise ExpresionNoPermitida("Solo se admiten funciones matematicas simples.")
        nombre = nodo.func.id
        if nombre not in _FUNCIONES_PERMITIDAS:
            raise ExpresionNoPermitida(
                f"La funcion {nombre} no esta permitida. Disponibles: "
                f"{', '.join(sorted(_FUNCIONES_PERMITIDAS))}."
            )
        if nodo.keywords:
            raise ExpresionNoPermitida("No se admiten argumentos con nombre.")
        argumentos = [_evaluar_nodo(a, profundidad + 1) for a in nodo.args]
        return _FUNCIONES_PERMITIDAS[nombre](*argumentos)

    raise ExpresionNoPermitida(
        "La expresion contiene algo que no es una operacion matematica."
    )


def calcular(expresion: str) -> str:
    """Resuelve una operacion matematica de forma exacta y sin eval."""
    if not isinstance(expresion, str) or not expresion.strip():
        return "No me llego ninguna operacion que calcular."

    expresion = expresion.strip()
    if len(expresion) > _LARGO_MAXIMO_EXPRESION:
        return "Esa operacion es demasiado larga para resolverla aqui."

    try:
        arbol = ast.parse(expresion, mode="eval")
    except SyntaxError:
        return (
            f"No pude entender la operacion {expresion}. Escribela como una cuenta de "
            "Python, por ejemplo 3340 ** 0.5 o sqrt(3340)."
        )

    if sum(1 for _ in ast.walk(arbol)) > _NODOS_MAXIMOS:
        return "Esa operacion tiene demasiadas partes para resolverla aqui."

    try:
        resultado = _evaluar_nodo(arbol)
    except ExpresionNoPermitida as motivo:
        return f"No puedo calcular eso. {motivo}"
    except ZeroDivisionError:
        return "No se puede dividir entre cero."
    except (ValueError, OverflowError) as motivo:
        return f"Esa operacion no tiene un resultado valido: {motivo}."
    except Exception:  # noqa: BLE001 - una herramienta nunca revienta hacia afuera
        return "No pude resolver esa operacion."

    return f"El resultado exacto de {expresion} es {_formatear(resultado)}."


def _formatear(valor) -> str:
    """Redondea para que la voz no lea veinte decimales, sin mentir sobre el numero."""
    if isinstance(valor, float):
        if valor.is_integer():
            return str(int(valor))
        redondeado = round(valor, 6)
        if redondeado == valor:
            return f"{redondeado:g}"
        # Si redondear cambio el valor, se dice que es aproximado. Leer en voz alta
        # veinte decimales no ayuda a nadie, pero afirmar que es exacto seria falso.
        return f"aproximadamente {redondeado:g}"
    return str(valor)


# ===========================================================================
# hora - un modelo de lenguaje no tiene reloj
# ===========================================================================
#
# Esta en la lista de "funciones reales" de la seccion 5.2 del enunciado, junto al
# clima y la busqueda web. Es la misma clase de limitacion que la calculadora: el
# modelo aprendio de textos escritos en el pasado y no tiene forma de saber que dia es
# hoy. Preguntado a secas, se inventa una fecha con total seguridad.

_DIAS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")
_MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def hora(ahora=None) -> str:
    """Hora y fecha del reloj de esta maquina, en una frase para decir en voz alta.

    `ahora` se inyecta en las pruebas: sin eso habria que comparar contra el reloj
    real y la prueba fallaria un dia al ano, a medianoche, sin que nadie entendiera
    por que.
    """
    from datetime import datetime

    ahora = ahora or datetime.now()

    # Las 14:05 se dicen "dos y cinco de la tarde", no "catorce cero cinco". Se lee en
    # voz alta: los numeros de reloj de 24 horas suenan a locutor de aeropuerto.
    hora24 = ahora.hour
    minuto = ahora.minute
    if hora24 < 6:
        franja = "de la madrugada"
    elif hora24 < 12:
        franja = "de la manana"
    elif hora24 < 20:
        franja = "de la tarde"
    else:
        franja = "de la noche"

    hora12 = hora24 % 12 or 12
    if minuto == 0:
        reloj = f"{hora12} en punto {franja}"
    elif minuto == 30:
        reloj = f"{hora12} y media {franja}"
    elif minuto == 15:
        reloj = f"{hora12} y cuarto {franja}"
    else:
        reloj = f"{hora12} y {minuto} {franja}"

    fecha = (f"{_DIAS[ahora.weekday()]} {ahora.day} de {_MESES[ahora.month - 1]} "
             f"de {ahora.year}")
    return f"Son las {reloj}. Hoy es {fecha}."


# ===========================================================================
# estado_laptop - telemetria real, no inventada
# ===========================================================================

def estado_laptop() -> str:
    """Bateria, memoria y procesador de esta maquina, en tono conversacional."""
    try:
        import psutil
    except ImportError:
        return "No puedo consultar el estado de la laptop: falta la libreria psutil."

    partes: list[str] = []

    try:
        bateria = psutil.sensors_battery()
    except Exception:  # noqa: BLE001 - en equipos sin bateria esto puede fallar
        bateria = None

    if bateria is None:
        partes.append(
            "Este equipo no reporta bateria, asi que debe estar conectado a la corriente"
        )
    else:
        enchufada = " y esta enchufada" if bateria.power_plugged else " y no esta enchufada"
        partes.append(f"La bateria esta al {int(bateria.percent)} por ciento{enchufada}")

    try:
        memoria = psutil.virtual_memory()
        libres = memoria.available / (1024 ** 3)
        partes.append(
            f"la memoria RAM va al {int(memoria.percent)} por ciento, con "
            f"{libres:.1f} gigas libres"
        )
    except Exception:  # noqa: BLE001
        pass

    try:
        # Intervalo corto: medir la CPU exige dos lecturas separadas en el tiempo.
        carga = int(psutil.cpu_percent(interval=0.3))
        partes.append(f"y el procesador esta al {carga} por ciento")
    except Exception:  # noqa: BLE001
        pass

    if not partes:
        return "No pude leer el estado de la laptop en este momento."
    return ". ".join(partes) + "."


# ===========================================================================
# buscar_web - informacion posterior al entrenamiento del modelo
# ===========================================================================

MAXIMO_RESULTADOS_WEB = 4
LARGO_MAXIMO_RESUMEN = 300


def buscar_web(consulta: str, buscador=None) -> str:
    """Busca en DuckDuckGo y devuelve los primeros resultados resumidos.

    `buscador` se puede inyectar en las pruebas para no salir a la red.
    """
    if not isinstance(consulta, str) or not consulta.strip():
        return "No me llego ninguna consulta que buscar."
    consulta = consulta.strip()

    if buscador is None:
        try:
            from ddgs import DDGS
        except ImportError:
            return "No puedo buscar en internet: falta la libreria ddgs."
        buscador = DDGS().text

    # SE REINTENTA UNA VEZ, y no por adorno. Con la libreria anterior
    # (`duckduckgo_search`, descontinuada) la MISMA consulta devolvia unas veces cuatro
    # resultados y otras cero, sin lanzar ningun error. El modelo recibia una busqueda
    # vacia y contestaba que no tenia acceso a internet, que es exactamente lo que la
    # duena vio el 2026-08-23 preguntando por el Big Ben. Se migro a `ddgs`, que en
    # seis intentos seguidos respondio las seis veces, pero un buscador publico y
    # gratuito siempre puede tener un mal momento y esto se demuestra en vivo.
    resultados = []
    for intento in range(2):
        try:
            resultados = list(buscador(consulta, max_results=MAXIMO_RESULTADOS_WEB) or [])
        except Exception:  # noqa: BLE001 - sin red, bloqueo del buscador, cambio de API
            resultados = []
        if resultados:
            break
        if intento == 0:
            time.sleep(1.0)

    if not resultados:
        return (
            f"No pude completar la busqueda de {consulta}. Puede que no haya conexion "
            "a internet, o que el buscador este rechazando peticiones ahora mismo."
        )
    lineas = [f"Resultados de la busqueda de {consulta}:"]
    for indice, resultado in enumerate(resultados[:MAXIMO_RESULTADOS_WEB], start=1):
        titulo = str(resultado.get("title", "sin titulo")).strip()
        cuerpo = " ".join(str(resultado.get("body", "")).split())
        if len(cuerpo) > LARGO_MAXIMO_RESUMEN:
            cuerpo = cuerpo[:LARGO_MAXIMO_RESUMEN].rstrip() + "..."
        lineas.append(f"{indice}. {titulo}. {cuerpo}")
    return "\n".join(lineas)


# ===========================================================================
# clima - el dato que cualquiera le pide a un asistente de voz
# ===========================================================================
#
# Lo pidio la duena: "debe funcionar cuando le pregunto el clima, tal y como funciona
# Alexa". Es la peticion mas natural que recibe un asistente y no estaba cubierta.
#
# Se usa open-meteo porque NO EXIGE CLAVE DE API ni registro. Anadir otro proveedor con
# credenciales habria significado otra clave que guardar, otra que puede caducar la
# vispera de la sustentacion y otra linea de `.env` que explicar en el README.

URL_CLIMA = "https://api.open-meteo.com/v1/forecast"
URL_GEOCODIFICACION = "https://geocoding-api.open-meteo.com/v1/search"

# El servicio devuelve el estado del cielo como un numero (codigo WMO). Se traduce a
# palabras que se puedan LEER EN VOZ ALTA, que es el unico formato util aqui.
_CIELO_POR_CODIGO = {
    0: "despejado",
    1: "casi despejado", 2: "parcialmente nublado", 3: "nublado",
    45: "con niebla", 48: "con niebla helada",
    51: "con llovizna ligera", 53: "con llovizna", 55: "con llovizna intensa",
    56: "con llovizna helada", 57: "con llovizna helada intensa",
    61: "con lluvia ligera", 63: "con lluvia", 65: "con lluvia fuerte",
    66: "con lluvia helada", 67: "con lluvia helada fuerte",
    71: "con nieve ligera", 73: "con nieve", 75: "con nieve intensa",
    77: "con granizo",
    80: "con chubascos ligeros", 81: "con chubascos", 82: "con chubascos fuertes",
    85: "con chubascos de nieve", 86: "con chubascos de nieve intensos",
    95: "con tormenta", 96: "con tormenta y granizo", 99: "con tormenta y granizo fuerte",
}


def _buscar_ciudad(nombre: str, pedir):
    """Traduce un nombre de ciudad a coordenadas. Devuelve (etiqueta, lat, lon)."""
    r = pedir(URL_GEOCODIFICACION,
              {"name": nombre, "count": 1, "language": "es", "format": "json"})
    resultados = (r or {}).get("results") or []
    if not resultados:
        raise LookupError(nombre)
    sitio = resultados[0]
    etiqueta = sitio.get("name", nombre)
    pais = sitio.get("country")
    if pais and pais != etiqueta:
        etiqueta = f"{etiqueta}, {pais}"
    return etiqueta, sitio["latitude"], sitio["longitude"]


def clima(ciudad: str, pedir=None) -> str:
    """Devuelve el tiempo actual de una ciudad, en una frase para decir en voz alta.

    `pedir` se inyecta en las pruebas: recibe (url, parametros) y devuelve el JSON ya
    convertido a diccionario. Asi la suite no sale a internet.
    """
    if not isinstance(ciudad, str) or not ciudad.strip():
        return "No me dijiste de que ciudad quieres el clima."
    ciudad = ciudad.strip()

    if pedir is None:
        import httpx

        def pedir(url, parametros):
            respuesta = httpx.get(url, params=parametros, timeout=20)
            respuesta.raise_for_status()
            return respuesta.json()

    try:
        etiqueta, lat, lon = _buscar_ciudad(ciudad, pedir)
    except LookupError:
        return (
            f"No encontre ninguna ciudad que se llame {ciudad}. Prueba con el nombre "
            "completo, por ejemplo Guayaquil o Quito."
        )
    except Exception:  # noqa: BLE001 - sin red, servicio caido, respuesta rara
        return (
            "No pude consultar el clima ahora mismo. Puede que no haya conexion a "
            "internet."
        )

    try:
        datos = pedir(URL_CLIMA, {
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
            "timezone": "auto",
        })
        ahora = datos["current"]
    except Exception:  # noqa: BLE001
        return (
            f"Encontre {etiqueta}, pero no pude leer el clima ahora mismo. Intentalo "
            "de nuevo en un momento."
        )

    grados = round(ahora.get("temperature_2m", 0))
    sensacion = round(ahora.get("apparent_temperature", grados))
    humedad = ahora.get("relative_humidity_2m")
    cielo = _CIELO_POR_CODIGO.get(ahora.get("weather_code"), "sin datos del cielo")

    frase = f"En {etiqueta} hay {grados} grados y el cielo esta {cielo}"
    # La sensacion termica solo se menciona cuando difiere de verdad: repetir el mismo
    # numero dos veces en voz alta suena a error del asistente.
    if abs(sensacion - grados) >= 2:
        frase += f", aunque se sienten como {sensacion}"
    if humedad is not None:
        frase += f". La humedad es del {humedad} por ciento"
    return frase + "."


# ===========================================================================
# abrir_pagina - el unico sitio donde este proyecto lanza un proceso
# ===========================================================================



class UrlNoPermitida(ValueError):
    """La url no paso la validacion de la lista blanca."""


def validar_url(url: str) -> str:
    """Comprueba la url contra la lista blanca. Devuelve la url o levanta excepcion.

    SE VALIDA EL HOSTNAME QUE DEVUELVE urlparse, NO LA CADENA COMPLETA. Comprobar si
    el texto de la direccion contiene youtube.com dejaria pasar un dominio como
    youtube.com.sitio-ajeno.ru, que pertenece a otro dueno por completo. urlparse
    extrae el host real, que es lo unico que decide a donde se conecta el navegador.
    """
    if not isinstance(url, str) or not url.strip():
        raise UrlNoPermitida("No me llego ninguna direccion que abrir.")

    partes = urlparse(url.strip())

    if partes.scheme.lower() not in ("http", "https"):
        raise UrlNoPermitida(
            "Solo puedo abrir direcciones que empiecen por http o https."
        )

    host = (partes.hostname or "").lower()
    if not host:
        raise UrlNoPermitida("Esa direccion no tiene un sitio web reconocible.")

    if host not in DOMINIOS_PERMITIDOS:
        raise UrlNoPermitida(
            f"El sitio {host} no esta en la lista de sitios permitidos. Solo puedo "
            "abrir YouTube, Wikipedia, Google y GitHub."
        )

    return url.strip()


def _buscar_navegador():
    """Devuelve la ruta del primer navegador que encuentre, o None.

    SE BUSCA, NO SE ESCRIBE A FUEGO. La primera version tenia la ruta de Edge escrita
    en una constante. Funcionaba en esta maquina y era un problema en cualquier otra:
    la duena usa Brave, y una ruta fija de un navegador que la persona no usa es un
    detalle que se nota en una demostracion.

    El orden es deliberado: primero Brave, que es el que usa ella; despues Edge, que
    viene con Windows y por lo tanto existe siempre; y Chrome al final. Los tres son
    Chromium, asi que aceptan los mismos interruptores.

    Si no hay ninguno, `abrir_pagina` cae al navegador predeterminado del sistema, que
    funciona en cualquier maquina aunque sin control de la ventana.
    """
    import os
    from pathlib import Path

    programas = os.environ.get("ProgramFiles", r"C:\Program Files")
    programas86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local = os.environ.get("LOCALAPPDATA", "")

    candidatos = [
        Path(local) / r"BraveSoftware\Brave-Browser\Application\brave.exe",
        Path(programas) / r"BraveSoftware\Brave-Browser\Application\brave.exe",
        Path(programas86) / r"BraveSoftware\Brave-Browser\Application\brave.exe",
        Path(programas86) / r"Microsoft\Edge\Application\msedge.exe",
        Path(programas) / r"Microsoft\Edge\Application\msedge.exe",
        Path(programas) / r"Google\Chrome\Application\chrome.exe",
        Path(programas86) / r"Google\Chrome\Application\chrome.exe",
    ]
    for ruta in candidatos:
        try:
            if ruta.is_file():
                return str(ruta)
        except OSError:
            continue
    return None


def construir_comando(url_validada, ruta_navegador=None):
    """Arma el comando como LISTA de argumentos. Nunca como una cadena.

    Es la diferencia entre que el sistema trate la direccion como un dato o como parte
    de una linea de ordenes. Con una lista y sin shell, unos caracteres raros dentro de
    la direccion son solo caracteres raros.

    VENTANA NORMAL, NO PANTALLA COMPLETA. Las dos primeras versiones abrian el navegador
    en modo kiosco. Funcionaba, y era un fastidio de usar: ocupaba la pantalla entera,
    sin barra de titulo ni boton de cerrar, y la duena se quedaba atrapada sin saber
    como salir. "Cierrala con Alt+F4" no es una respuesta: si hay que explicar como
    salir de algo, ese algo esta mal hecho.

    LA DIRECCION VA COMO ARGUMENTO SUELTO, NO PEGADA CON UN IGUAL. La primera version
    generaba `--kiosk=https://...` y el navegador abria su pagina de inicio en lugar de
    la pedida: en Chromium esos interruptores no llevan valor, asi que al pegarle un
    `=algo` la direccion se perdia. Ninguna prueba lo habria visto, porque el comando
    estaba bien FORMADO; lo que estaba mal era su significado para quien lo recibe.

    `--no-first-run` evita que en un perfil recien creado el navegador se plante en su
    asistente de bienvenida antes de mostrar nada.
    """
    navegador = ruta_navegador or _buscar_navegador()
    if navegador is None:
        return None
    return [
        navegador,
        "--new-window",
        url_validada,
        "--start-maximized",
        "--no-first-run",
    ]


def abrir_pagina(url, lanzar=None, ruta_navegador=None):
    """Abre una url permitida en una ventana del navegador.

    `lanzar` se inyecta en las pruebas: se verifica que el comando este bien armado
    **sin abrir ningun navegador de verdad**, que es lo que pide el criterio de T-15.
    """
    try:
        url_validada = validar_url(url)
    except UrlNoPermitida as motivo:
        return str(motivo)

    comando = construir_comando(url_validada, ruta_navegador)

    if comando is None:
        # Ningun navegador conocido instalado. Se abre con el predeterminado del
        # sistema, que existe siempre; se pierde el control de la ventana y no importa.
        try:
            import webbrowser
            webbrowser.open(url_validada)
        except Exception:  # noqa: BLE001
            return "No encontre ningun navegador para abrir la pagina."
        return "Listo, ya tienes " + url_validada + " abierta en el navegador."

    if lanzar is None:
        def lanzar(cmd):
            # shell=False es el valor por defecto y se deja explicito porque es la
            # decision de seguridad de esta linea, no un detalle de estilo.
            return subprocess.Popen(cmd, shell=False)

    try:
        lanzar(comando)
    except FileNotFoundError:
        return "No encontre el navegador en esta computadora, asi que no pude abrir la pagina."
    except Exception:  # noqa: BLE001
        return "No pude abrir la pagina en el navegador."

    return "Listo, ya tienes " + url_validada + " abierta en el navegador."


# ===========================================================================
# Control del sistema: volumen, brillo, carpetas y YouTube
# ===========================================================================
#
# Anadidas el 2026-08-27 a peticion de la duena, que vio estas mismas funciones en el
# proyecto de un companero. La seccion 5.2 del enunciado las contempla entre los
# valores agregados: "integracion con funciones reales" y "control de archivos locales".
#
# MISMO CRITERIO DE SEGURIDAD QUE EN EL RESTO DEL ARCHIVO: nada de rutas arbitrarias ni
# de comandos construidos con texto del modelo. Las carpetas salen de una lista cerrada
# y el brillo se valida como entero antes de tocar nada. Un asistente que abre "la
# carpeta que le digas" es un asistente que abre una carpeta del sistema el dia que la
# transcripcion salga mal.

# Codigos de tecla multimedia de Windows. Se usan las teclas y no la API de audio a
# proposito: keybd_event vive en user32, que ya viene con el sistema, mientras que
# manejar el volumen por COM exige mas codigo y una dependencia. Para subir y bajar,
# que es lo que se pide, las teclas hacen exactamente lo mismo.
_TECLA_SILENCIO = 0xAD
_TECLA_BAJAR = 0xAE
_TECLA_SUBIR = 0xAF

# Cada pulsacion mueve el volumen dos puntos. Diez pulsaciones son un 20 %, que es un
# salto que se nota al oido sin pasarse.
_PULSACIONES_POR_PASO = 10

# El brillo se mueve de veinte en veinte: los saltos pequenos no se aprecian y obligan
# a repetir la orden tres veces.
_PASO_BRILLO = 20


def _pulsar(tecla, veces=1):
    import ctypes
    for _ in range(veces):
        ctypes.windll.user32.keybd_event(tecla, 0, 0, 0)   # tecla abajo
        ctypes.windll.user32.keybd_event(tecla, 0, 2, 0)   # tecla arriba


def volumen(accion, pulsar=None):
    """Sube, baja o silencia el volumen del sistema.

    `pulsar` se inyecta en las pruebas para no mover el volumen de verdad mientras
    corre la suite.
    """
    accion = (accion or "").strip().lower()
    pulsar = pulsar or _pulsar
    try:
        if accion in ("subir", "sube", "mas", "aumentar", "alto"):
            pulsar(_TECLA_SUBIR, _PULSACIONES_POR_PASO)
            return "Listo, subi el volumen."
        if accion in ("bajar", "baja", "menos", "reducir", "bajo"):
            pulsar(_TECLA_BAJAR, _PULSACIONES_POR_PASO)
            return "Listo, baje el volumen."
        if accion in ("silenciar", "silencio", "mutear", "quitar", "mute"):
            pulsar(_TECLA_SILENCIO, 1)
            return "Listo, silencie el sonido. Dime que lo actives para volver a oirme."
        return "No entendi que hacer con el volumen. Puedo subirlo, bajarlo o silenciarlo."
    except Exception:  # noqa: BLE001 - una herramienta nunca revienta hacia afuera
        return "No pude cambiar el volumen en este momento."


def _leer_brillo():
    import subprocess
    salida = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness)"
         ".CurrentBrightness"],
        capture_output=True, text=True, timeout=15, shell=False,
    )
    return int(salida.stdout.strip().splitlines()[0])


def _fijar_brillo(nivel):
    import subprocess
    # `nivel` ya viene validado por quien llama. Se vuelve a forzar aqui porque es lo
    # unico de este comando que no es texto fijo: es la linea por la que entraria una
    # inyeccion si algun dia se llamara desde otro sitio sin validar.
    nivel = max(0, min(100, int(nivel)))
    # Invoke-CimMethod y NO llamar al metodo sobre el objeto. La primera version hacia
    # `(Get-CimInstance ...).WmiSetBrightness(1,60)` y fallaba siempre: Get-CimInstance
    # devuelve un CimInstance, que es solo datos y no expone los metodos de la clase
    # WMI. El comando parecia razonable y no lo era; se vio ejecutandolo, no leyendolo.
    orden = (
        "Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods | "
        "Invoke-CimMethod -MethodName WmiSetBrightness "
        "-Arguments @{Timeout=1;Brightness=" + str(nivel) + "}"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", orden],
        capture_output=True, text=True, timeout=20, shell=False, check=True,
    )


def brillo(accion, leer=None, fijar=None):
    """Sube o baja el brillo de la pantalla.

    `leer` y `fijar` se inyectan en las pruebas: sin eso la suite cambiaria el brillo
    de la pantalla de quien la ejecuta, que es de las cosas mas molestas que puede
    hacer un conjunto de pruebas.
    """
    accion = (accion or "").strip().lower()
    if accion in ("subir", "sube", "mas", "aumentar", "alto"):
        delta = _PASO_BRILLO
    elif accion in ("bajar", "baja", "menos", "reducir", "bajo"):
        delta = -_PASO_BRILLO
    else:
        return "No entendi que hacer con el brillo. Puedo subirlo o bajarlo."

    try:
        actual = (leer or _leer_brillo)()
    except Exception:  # noqa: BLE001
        return ("Esta pantalla no deja cambiar el brillo por software. Suele pasar con "
                "los monitores externos.")

    objetivo = max(0, min(100, actual + delta))
    if objetivo == actual:
        borde = "al maximo" if objetivo == 100 else "al minimo"
        return "El brillo ya esta " + borde + "."

    try:
        (fijar or _fijar_brillo)(objetivo)
    except Exception:  # noqa: BLE001
        return "No pude cambiar el brillo en este momento."
    return "Listo, deje el brillo en " + str(objetivo) + " por ciento."


def _carpetas_conocidas():
    """Lista CERRADA de carpetas, con el mismo criterio que la lista blanca de dominios.

    El modelo pide una de estas por su nombre, no una ruta. Si la transcripcion sale
    mal, lo peor que ocurre es que no encuentre la carpeta.

    LAS RUTAS SE LE PREGUNTAN A WINDOWS, no se construyen a mano. La primera version
    hacia Path.home() mas el nombre en ingles, y en esta maquina fallaba: OneDrive tiene
    redirigidos el Escritorio y las Imagenes, que viven dentro de la carpeta de OneDrive
    y no en el perfil del usuario. Windows guarda las rutas de verdad en el registro y
    ahi es donde hay que leerlas. Suponer donde vive una carpeta del usuario funciona
    hasta que alguien tiene OneDrive, otro idioma, o las carpetas movidas de sitio.
    """
    import os
    import winreg
    from pathlib import Path

    # Nombre que dice la usuaria -> clave con la que Windows guarda esa ruta.
    CLAVES = {
        "descargas": "{374DE290-123F-4565-9164-39C4925E467B}",
        "documentos": "Personal",
        "escritorio": "Desktop",
        "imagenes": "My Pictures",
        "musica": "My Music",
        "videos": "My Video",
    }
    RUTA_REGISTRO = (
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
    )

    carpetas = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUTA_REGISTRO) as llave:
            for nombre, clave in CLAVES.items():
                try:
                    valor, _ = winreg.QueryValueEx(llave, clave)
                    carpetas[nombre] = Path(os.path.expandvars(valor))
                except OSError:
                    continue
    except OSError:
        # Si el registro no se deja leer, se cae a lo evidente: sirve en una maquina
        # sin OneDrive y no empeora nada en una con el.
        casa = Path.home()
        carpetas = {
            "descargas": casa / "Downloads", "documentos": casa / "Documents",
            "escritorio": casa / "Desktop", "imagenes": casa / "Pictures",
            "musica": casa / "Music", "videos": casa / "Videos",
        }

    carpetas["proyecto"] = Path(__file__).resolve().parents[1]
    return carpetas


def abrir_carpeta(nombre, abrir=None):
    """Abre en el explorador una de las carpetas conocidas."""
    import unicodedata

    if not isinstance(nombre, str) or not nombre.strip():
        return "No me dijiste que carpeta abrir."

    # Se quitan los acentos antes de comparar: la transcripcion de voz escribe
    # "imagenes" o "imagenes" con tilde segun el dia, y son la misma carpeta.
    limpio = "".join(
        c for c in unicodedata.normalize("NFD", nombre.strip().lower())
        if unicodedata.category(c) != "Mn"
    )

    carpetas = _carpetas_conocidas()
    destino = carpetas.get(limpio)
    if destino is None:
        for clave, ruta in carpetas.items():
            if clave in limpio or limpio in clave:
                destino, limpio = ruta, clave
                break

    if destino is None:
        return ("No conozco ninguna carpeta que se llame " + nombre + ". Puedo abrir: "
                + ", ".join(sorted(carpetas)) + ".")
    if not destino.exists():
        return "La carpeta " + limpio + " no existe en esta computadora."

    try:
        if abrir is not None:
            abrir(destino)
        else:
            import os
            os.startfile(destino)
    except Exception:  # noqa: BLE001
        return "No pude abrir la carpeta " + limpio + "."
    return "Listo, abri la carpeta " + limpio + "."


def reproducir_youtube(busqueda, lanzar=None):
    """Busca algo en YouTube y abre los resultados en el navegador.

    Se abre la BUSQUEDA y no un video concreto a proposito: para saber cual es el video
    correcto habria que consultar la API de YouTube, que exige clave, cuota y otra
    dependencia. Abrir la busqueda deja elegir a la persona, que es lo que cualquiera
    hace de todos modos.
    """
    from urllib.parse import quote_plus

    if not isinstance(busqueda, str) or not busqueda.strip():
        return "No me dijiste que buscar en YouTube."

    consulta = quote_plus(busqueda.strip())
    url = "https://www.youtube.com/results?search_query=" + consulta
    # Pasa por la MISMA validacion de lista blanca que abrir_pagina. La url la
    # construimos nosotros, pero validarla igual no cuesta nada y evita que un cambio
    # futuro se salte el control sin que nadie lo note.
    return abrir_pagina(url, lanzar=lanzar)

# ===========================================================================
# Despachador: el unico punto por el que una peticion del modelo se ejecuta
# ===========================================================================

_IMPLEMENTACIONES = {
    "calcular": lambda a: calcular(a.get("expresion", "")),
    "clima": lambda a: clima(a.get("ciudad", "")),
    "hora": lambda a: hora(),
    "volumen": lambda a: volumen(a.get("accion", "")),
    "brillo": lambda a: brillo(a.get("accion", "")),
    "abrir_carpeta": lambda a: abrir_carpeta(a.get("carpeta", "")),
    "reproducir_youtube": lambda a: reproducir_youtube(a.get("busqueda", "")),
    "estado_laptop": lambda a: estado_laptop(),
    "buscar_web": lambda a: buscar_web(a.get("consulta", "")),
    "abrir_pagina": lambda a: abrir_pagina(a.get("url", "")),
}


def ejecutar_herramienta(peticion) -> str:
    """Ejecuta una PeticionDeTool contra la lista cerrada de herramientas.

    Es la funcion que el orquestador recibe como `ejecutar_herramienta`. Si el modelo
    inventa un nombre de herramienta -cosa que hacen- no pasa nada: no esta en el
    diccionario y se le devuelve una frase diciendoselo. El modelo nunca alcanza a
    ejecutar algo que no este declarado aqui.
    """
    nombre = getattr(peticion, "nombre", "")
    argumentos = getattr(peticion, "argumentos", None) or {}
    if not isinstance(argumentos, dict):
        argumentos = {}

    implementacion = _IMPLEMENTACIONES.get(nombre)
    if implementacion is None:
        return (
            f"La herramienta {nombre} no existe. Las disponibles son: "
            f"{', '.join(sorted(_IMPLEMENTACIONES))}."
        )

    try:
        return implementacion(argumentos)
    except Exception:  # noqa: BLE001 - ninguna herramienta tumba el turno
        return f"La herramienta {nombre} no pudo completarse."
