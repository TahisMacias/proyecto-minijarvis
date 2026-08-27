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
NOMBRE_ABRIR_PAGINA = "abrir_pagina"
NOMBRE_CALCULAR = "calcular"
NOMBRE_CLIMA = "clima"
NOMBRE_HORA = "hora"
NOMBRE_VOLUMEN = "volumen"
NOMBRE_BRILLO = "brillo"
NOMBRE_ABRIR_CARPETA = "abrir_carpeta"
NOMBRE_YOUTUBE = "reproducir_youtube"


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
            "name": NOMBRE_CLIMA,
            "description": (
                "Consulta el tiempo que hace AHORA MISMO en una ciudad: temperatura, "
                "sensacion termica, humedad y estado del cielo. USA SIEMPRE esta "
                "herramienta cuando pregunten por el clima, el tiempo, si llueve, si "
                "hace frio o calor, o que temperatura hay. No lo respondas de memoria: "
                "el clima cambia cada hora y tu no puedes saberlo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ciudad": {
                        "type": "string",
                        "description": (
                            "Nombre de la ciudad. Si la persona no dice ninguna, usa "
                            "Guayaquil, que es donde esta la usuaria."
                        ),
                    }
                },
                "required": ["ciudad"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": NOMBRE_HORA,
            "description": (
                "Dice la hora y la fecha de ahora mismo, leidas del reloj de esta "
                "computadora. USA SIEMPRE esta herramienta cuando pregunten la hora, "
                "el dia, la fecha, en que mes o ano estamos, o cuanto falta para algo. "
                "No lo respondas de memoria: tu no tienes reloj y no sabes que dia es "
                "hoy."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
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
            "name": NOMBRE_VOLUMEN,
            "description": (
                "Sube, baja o silencia el volumen de esta computadora. Usala cuando "
                "te pidan mas volumen, menos volumen, que subas o bajes el sonido, o "
                "que silencies."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "enum": ["subir", "bajar", "silenciar"],
                        "description": "Que hacer con el volumen.",
                    }
                },
                "required": ["accion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": NOMBRE_BRILLO,
            "description": (
                "Sube o baja el brillo de la pantalla. Usala cuando te digan que la "
                "pantalla esta muy oscura o muy clara, o que subas o bajes el brillo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "enum": ["subir", "bajar"],
                        "description": "Que hacer con el brillo.",
                    }
                },
                "required": ["accion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": NOMBRE_ABRIR_CARPETA,
            "description": (
                "Abre una carpeta en el explorador de archivos. Solo puede abrir estas: "
                "descargas, documentos, escritorio, imagenes, musica, videos y la "
                "carpeta del proyecto. Si te piden otra, dilo con naturalidad."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "carpeta": {
                        "type": "string",
                        "enum": ["descargas", "documentos", "escritorio", "imagenes",
                                 "musica", "videos", "proyecto"],
                        "description": "Cual de las carpetas conocidas abrir.",
                    }
                },
                "required": ["carpeta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": NOMBRE_YOUTUBE,
            "description": (
                "Busca algo en YouTube y lo abre en el navegador. Usala cuando te "
                "pidan poner, buscar o reproducir una cancion, un video o un artista. "
                "Abre la pagina de resultados para que la persona elija cual ver."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "busqueda": {
                        "type": "string",
                        "description": (
                            "Que buscar en YouTube: el nombre de la cancion, el "
                            "artista o el tema del video."
                        ),
                    }
                },
                "required": ["busqueda"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": NOMBRE_ABRIR_PAGINA,
            "description": (
                "Abre una pagina web en una ventana del navegador. Solo "
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
