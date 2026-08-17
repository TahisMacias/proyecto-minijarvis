"""Declaracion de las herramientas que el modelo puede pedir (tarea T-15).

QUE ES EL TOOL CALLING, EN UNA FRASE: el modelo no ejecuta nada. Lo unico que hace es
DECIR, en un JSON, "quiero llamar a `calcular` con la expresion 3340**0.5". Nuestro
codigo lee ese JSON, comprueba que la herramienta exista en esta lista cerrada, la
ejecuta el mismo y le devuelve el resultado al modelo para que lo redacte. Entre lo
que el modelo pide y lo que la maquina hace siempre hay codigo nuestro decidiendo.

POR QUE ESTE ARCHIVO ESTA SEPARADO DE LA IMPLEMENTACION: aqui vive la DESCRIPCION que
el modelo lee para decidir cuando usar cada herramienta; en `system_skills.py` vive lo
que la herramienta HACE. Separarlos deja claro que el manifiesto es texto que viaja al
modelo, y por lo tanto no debe contener nada sensible ni nada que el modelo no deba
saber.

COMO SE ESCRIBE UNA BUENA DESCRIPCION: el modelo elige la herramienta leyendo estas
frases, nada mas. Una descripcion vaga produce llamadas a destiempo. Por eso cada una
dice cuando SI y, cuando importa, cuando NO. La de `calcular` es la mas explicita a
proposito: existe justamente porque el modelo intentaba resolver cuentas de cabeza.
"""

from __future__ import annotations

NOMBRE_ESTADO_LAPTOP = "estado_laptop"
NOMBRE_BUSCAR_WEB = "buscar_web"
NOMBRE_ABRIR_KIOSK = "abrir_kiosk"
NOMBRE_CALCULAR = "calcular"


MANIFIESTO: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": NOMBRE_CALCULAR,
            "description": (
                "Resuelve una operacion matematica con precision exacta. USA SIEMPRE "
                "esta herramienta cuando te pidan una cuenta: raices, potencias, "
                "porcentajes, multiplicaciones largas, divisiones. No calcules de "
                "cabeza ni des resultados aproximados: eres un modelo de lenguaje y "
                "predices texto, no calculas. Ejemplos de expresion valida: "
                "'3340 ** 0.5' para la raiz cuadrada de 3340, 'sqrt(3340)', "
                "'15 * 1.12', '(2400 / 12) * 3'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expresion": {
                        "type": "string",
                        "description": (
                            "La operacion en notacion de Python. Operadores: + - * / "
                            "// % **. Funciones disponibles: sqrt, abs, round, min, "
                            "max, pow, log, log10, exp, sin, cos, tan, floor, ceil. "
                            "Constantes: pi, e. Solo numeros y operaciones: nada de "
                            "nombres de variables ni de texto."
                        ),
                    }
                },
                "required": ["expresion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": NOMBRE_ESTADO_LAPTOP,
            "description": (
                "Consulta el estado real de esta computadora: porcentaje de bateria y "
                "si esta enchufada, memoria RAM en uso y carga del procesador. Usala "
                "cuando pregunten como esta la laptop, cuanta bateria queda o si el "
                "equipo esta cargado de trabajo. Devuelve datos medidos, no estimados."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": NOMBRE_BUSCAR_WEB,
            "description": (
                "Busca informacion actual en internet y devuelve los primeros "
                "resultados con su titulo y un resumen. Usala cuando te pregunten por "
                "hechos recientes, noticias, precios o cualquier dato que pueda haber "
                "cambiado despues de tu entrenamiento. No la uses para conocimiento "
                "general estable ni para cuentas matematicas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "Que buscar, en pocas palabras.",
                    }
                },
                "required": ["consulta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": NOMBRE_ABRIR_KIOSK,
            "description": (
                "Abre una pagina web en el navegador, a pantalla completa. Solo "
                "funciona con una lista corta de sitios permitidos: YouTube, "
                "Wikipedia, Google y GitHub. Si te piden abrir cualquier otro sitio, "
                "la herramienta lo rechazara: dilo con naturalidad en vez de insistir."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "Direccion completa, empezando por https://. Por ejemplo "
                            "https://es.wikipedia.org/wiki/Transformer"
                        ),
                    }
                },
                "required": ["url"],
            },
        },
    },
]


NOMBRES_DECLARADOS = frozenset(
    entrada["function"]["name"] for entrada in MANIFIESTO
)
