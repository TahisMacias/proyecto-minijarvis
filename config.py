"""Configuracion central de Mini-JARVIS.

Este modulo es la unica fuente de verdad de configuracion del proyecto: carga la
clave de API desde el archivo .env de la raiz, valida que exista y expone como
constantes de modulo la paleta de colores, los identificadores de los modelos,
los limites de memoria y tool calling, y la lista blanca de dominios para la
herramienta abrir_kiosk.

Ningun otro modulo debe leer variables de entorno ni redefinir estas constantes
por su cuenta: todos importan de aqui.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


class ConfiguracionInvalida(RuntimeError):
    """Se levanta cuando falta o es invalida una variable de configuracion requerida."""


# --- Carga de variables de entorno -----------------------------------------
# La ruta se ancla a la ubicacion de este archivo, no al directorio de trabajo,
# para que el modulo funcione sin importar desde donde se ejecute la app.
RUTA_ENV = Path(__file__).resolve().parent / ".env"

# override=False: si la variable ya existe en el entorno de la sesion (por
# ejemplo, inyectada por quien ejecuta pruebas), esa tiene prioridad sobre el
# valor del archivo .env. Asi se puede probar el modulo sin tocar .env.
load_dotenv(RUTA_ENV, override=False)


def _leer_api_key() -> str:
    """Lee y valida TOGETHER_API_KEY del entorno despues de cargar dotenv.

    Levanta ConfiguracionInvalida si la variable no existe, esta vacia o
    contiene solo espacios en blanco. Nunca deja escapar un KeyError ni
    incluye el valor leido en el mensaje de error.
    """
    valor = os.environ.get("TOGETHER_API_KEY")
    if valor is None or valor.strip() == "":
        raise ConfiguracionInvalida(
            "Falta la variable TOGETHER_API_KEY. Debe definirse en el archivo "
            ".env de la raiz del repositorio (usa .env.example como plantilla)."
        )
    return valor


# Se valida al importar, no en una funcion que alguien podria olvidar llamar:
# el diseno exige que la app no arranque a medias sin credenciales.
TOGETHER_API_KEY = _leer_api_key()


# --- Paleta pastel (diseno, seccion 11) -------------------------------------
PALETA = {
    "fondo_crema": "#F9F9FB",
    "verde_menta": "#E8F5E9",
    "rosa_palido": "#FCE4EC",
    "azul_cielo": "#E1F5FE",
    "durazno": "#FFF3E0",
    "texto_gris_marengo": "#37474F",
}

# Los cinco acentos son tintes Material de nivel 50 (green, pink, light-blue,
# orange). Mantener ese nivel al anadir cualquier color nuevo: es lo que da
# coherencia visual a la paleta.

# Mapeo estado -> color segun la tabla de estados del diseno (seccion 11).
# Cada estado tiene color propio: que dos compartan color reprueba H-09, que
# exige distinguir los cuatro estados sin leer texto, y deja fuera a personas
# con daltonismo. La GUI (T-10) debe ademas diferenciarlos por forma.
COLOR_POR_ESTADO = {
    "ESCUCHANDO": PALETA["verde_menta"],
    "PENSANDO": PALETA["azul_cielo"],
    "RESPONDIENDO": PALETA["rosa_palido"],
    "ATENCION": PALETA["durazno"],
}

# Borde saturado de cada estado, del MISMO tono que su relleno pastel.
#
# POR QUE HACE FALTA (defecto reportado por la duena el 2026-08-14): los tintes de
# nivel 50 son tan palidos que en pantalla se leen casi blancos. Probando la
# aplicacion, el verde menta de ESCUCHANDO se veia azul. Como decoracion los pasteles
# funcionan; como SENAL no: si el usuario no puede nombrar el color, el color no esta
# comunicando nada.
#
# La solucion conserva el aspecto pastel de la ventana (el relleno no cambia) y pone
# la carga de la senal en un borde grueso y saturado. Son los tintes Material 700-800
# de las mismas familias que los rellenos, asi que el sistema de color sigue siendo
# coherente: verde con verde, azul con azul, rosa con rosa, naranja con naranja.
COLOR_BORDE_POR_ESTADO = {
    "ESCUCHANDO": "#2E7D32",    # green 800
    "PENSANDO": "#0277BD",      # light-blue 800
    "RESPONDIENDO": "#C2185B",  # pink 700
    "ATENCION": "#EF6C00",      # orange 800
}


# --- Proveedor y modelos (diseno, seccion 4) --------------------------------
TOGETHER_BASE_URL = "https://api.together.xyz/v1"

# ELEGIDOS PROBANDO CONTRA LA API REAL. Aparecer en GET /v1/models NO significa estar
# disponible: los identificadores "grandes" mas obvios (Qwen2.5-72B-Instruct,
# Qwen3-Next-80B, Qwen3.6-Plus, Qwen3.7-Max...) devuelven HTTP 400 "Unable to access
# non-serverless model". Estan en el catalogo de Together, no en su servicio
# compartido: usarlos exigiria pagar un endpoint dedicado. Se probaron 26
# identificadores uno por uno; solo estos dos responden y sirven para el proyecto.
#
# Qwen3.8-2.4T-A95B es un modelo de razonamiento: antes de responder escribe su
# propio borrador de pensamiento, que la API devuelve aparte en un campo `reasoning`.
# Cuesta mas tokens de salida que un modelo normal, pero razona mejor y responde en
# ~2.5 s, que es aceptable para voz. No existe ninguna variante de 27B en Together.
MODELO_LLM_PREDETERMINADO = "Qwen/Qwen3.8-2.4T-A95B"

# El alterno es a proposito MUCHO mas pequeno: el contraste entre un modelo enorme y
# uno de 7B se nota en vivo, y es lo que hace util el selector durante la sustentacion.
MODELO_LLM_ALTERNO = "Qwen/Qwen2.5-7B-Instruct-Turbo"

# Precio por millon de tokens en Together, consultado el 2026-08-14. Se anota aqui
# porque el saldo es limitado y conviene saber que cuesta cada turno.
#   Qwen3.8-2.4T-A95B          entrada $2.50   salida $6.25
#   Qwen2.5-7B-Instruct-Turbo  entrada $0.30   salida $0.30
#   whisper-large-v3           $0.0015 por minuto de audio

MODELO_STT = "openai/whisper-large-v3"
IDIOMA_STT = "es"

VOZ_TTS = "es-MX-DaliaNeural"

# Ajustes de la voz. edge-tts permite subir el tono y acelerar el habla sin cambiar de
# voz. Subir el tono acerca el resultado al registro agudo y brillante del personaje
# que la duena pidió como tematica, sin necesidad de clonar ninguna voz real.
# Valores conservadores: mas alla de +50Hz la voz empieza a sonar metalica y se pierde
# claridad, que es lo ultimo que conviene en un asistente que se escucha por altavoz.
TONO_TTS = "+35Hz"
RITMO_TTS = "+8%"


# --- Captura de audio (correccion del 2026-08-14) ---------------------------
# Whisper ALUCINA con audio vacio: ante silencio devuelve muletillas como "Gracias" o
# "Subtitulos realizados por...". Lo detecto la duena pulsando y soltando sin hablar.
# La defensa es no enviarle nada que no tenga voz dentro: se exige una duracion minima
# y un volumen minimo. De paso ahorra dinero, porque cada envio se paga.
DURACION_MINIMA_GRABACION = 0.35  # segundos

# Volumen medio (RMS) por debajo del cual se considera que no se hablo. Las muestras
# son enteros de 16 bits (-32768 a 32767); el ruido de fondo de un portatil ronda 30-80
# y la voz normal pasa de 500 con holgura.
UMBRAL_DE_SILENCIO = 180


# --- Interfaz (correccion del 2026-08-14) -----------------------------------
# Cuanto se queda a la vista el estado ATENCION antes de volver a reposo. Antes la
# transicion era instantanea: el estado ocurria, pero duraba microsegundos y nadie lo
# veia nunca. Un aviso que no se alcanza a ver no es un aviso.
SEGUNDOS_EN_ATENCION = 2.5


# --- Memoria conversacional (diseno, seccion 8) -----------------------------
# Se conservan los ultimos 10 turnos (usuario + asistente); al superarlos se
# descarta el par mas antiguo.
MAX_TURNOS_MEMORIA = 10


# --- Tool calling (diseno, seccion 7) ---------------------------------------
# Maximo de rondas de tool calling por turno: evita un bucle infinito si el
# modelo insiste en llamar herramientas. Al agotarse, responde con el texto
# que tenga.
LIMITE_RONDAS_TOOL_CALLING = 2

# Lista blanca de dominios para abrir_kiosk (diseno, seccion 9). Minusculas,
# sin esquema ni barra final. La fija el Ingeniero: no se amplia ni se reduce
# aqui. La logica de validacion de URL vive en tools/system_skills.py (T-15),
# fuera del alcance de este archivo.
DOMINIOS_PERMITIDOS_KIOSK = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "wikipedia.org",
        "es.wikipedia.org",
        "google.com",
        "www.google.com",
        "github.com",
        "www.github.com",
    }
)


# --- Muestreo del LLM (controles de sustentacion, seccion 11) --------------
# Valores por defecto pensados para un asistente conversacional: suficiente
# variedad en la redaccion para no sonar mecanico, sin volverse erratico ni
# perder coherencia. Los sliders de la GUI parten de aqui y el usuario los
# puede mover en vivo para demostrar su efecto.
TEMPERATURA_PREDETERMINADA = 0.7
TOP_P_PREDETERMINADO = 0.9
