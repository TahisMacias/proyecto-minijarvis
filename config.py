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


# --- Paleta (rediseno T-19, 2026-08-17) -------------------------------------
#
# CAMBIO DE TEMA, pedido por la duena: la interfaz pastel clara le parecia "limpia y
# profesional" pero sin personalidad. Se pasa a un tema OSCURO con la paleta del
# personaje que eligio como tematica: turquesa y rosa.
#
# NO SE USA NINGUN ARTE DE TERCEROS. El repositorio es publico y el diseno del
# personaje es propiedad de Crypton Future Media. Lo que se hace es tomar sus dos
# colores -que no son propiedad de nadie- y dibujar por codigo. Ver gui/desktop_app.py.
#
# LO QUE NO CAMBIA, PORQUE NO SE NEGOCIA (H-09): los cuatro estados se siguen
# distinguiendo por COLOR Y POR FORMA. Que dos compartan color sigue siendo NO APTO
# automatico. Lo que si se invirtio es la direccion del contraste: sobre fondo oscuro
# el borde legible es el CLARO, no el oscuro. La prueba de contraste se actualizo para
# medir la diferencia en valor absoluto en vez de asumir una direccion.
PALETA = {
    "fondo_profundo": "#101F27",   # el fondo de la ventana
    "superficie": "#18303B",       # paneles sobre el fondo
    "superficie_alta": "#1F3F4C",  # controles sobre los paneles
    "turquesa": "#39C5BB",         # el color del personaje; acento principal
    "rosa": "#FF6B9D",             # acento secundario
    "texto_claro": "#E8F6F5",
    "texto_tenue": "#8FB3B8",
}

# Relleno de cada estado: version apagada del color, para que la figura tenga cuerpo
# sin competir con el borde.
COLOR_POR_ESTADO = {
    "ESCUCHANDO": "#1F5F5B",    # turquesa apagado
    "PENSANDO": "#2A3D6B",      # azul profundo
    "RESPONDIENDO": "#6B2647",  # rosa apagado
    "ATENCION": "#6B4A1F",      # ambar apagado
}

# Borde luminoso de cada estado, del mismo tono que su relleno.
#
# POR QUE EXISTE (defecto que reporto la duena el 2026-08-14, y que sigue vigente en el
# tema oscuro): un color que el usuario no puede nombrar no esta comunicando nada. En el
# tema claro el problema era que los pasteles se leian casi blancos; aqui seria que los
# rellenos apagados se leen casi negros. La carga de la senal la lleva el borde.
COLOR_BORDE_POR_ESTADO = {
    "ESCUCHANDO": "#39C5BB",    # turquesa vivo
    "PENSANDO": "#7AA5FF",      # azul claro
    "RESPONDIENDO": "#FF6B9D",  # rosa vivo
    "ATENCION": "#FFB347",      # ambar
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
