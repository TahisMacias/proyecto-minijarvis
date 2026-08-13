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


# --- Proveedor y modelos (diseno, seccion 4) --------------------------------
TOGETHER_BASE_URL = "https://api.together.xyz/v1"

MODELO_LLM_PREDETERMINADO = "Qwen/Qwen2.5-72B-Instruct"
MODELO_LLM_ALTERNO = "meta-llama/Llama-3.3-70B-Instruct"

MODELO_STT = "openai/whisper-large-v3"
IDIOMA_STT = "es"

VOZ_TTS = "es-MX-DaliaNeural"


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
