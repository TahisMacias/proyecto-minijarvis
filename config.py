"""Configuracion central de Mini-JARVIS.

Este modulo es la unica fuente de verdad de configuracion del proyecto: carga la
clave de API desde el archivo .env de la raiz, valida que exista y expone como
constantes de modulo la paleta de colores, los identificadores de los modelos,
los limites de memoria y tool calling, y la lista blanca de dominios para la
herramienta abrir_pagina.

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


# --- Paleta (rediseno T-20 "neon minimo", 2026-08-23) ------------------------
#
# Tercera version del aspecto de la aplicacion, y esta vez elegida MIRANDO. Se le
# dibujaron tres bocetos -claro y amable, HUD estilo Iron Man, y neon
# minimo- y se eligio el tercero. Las dos versiones anteriores se disenaron adivinando lo
# que queria a partir de descripciones, y las dos fallaron.
#
# La idea de esta: casi todo el espacio vacio, una sola pieza protagonista, y el resto
# en texto fino con lineas de acento. Sin cajas ni recuadros: los paneles con borde son
# lo que hacia que la ventana pareciera un formulario.
#
# LO QUE NO CAMBIA CON EL TEMA (H-09): los cuatro estados se siguen distinguiendo por
# COLOR Y POR FORMA. Que dos compartan color sigue siendo NO APTO automatico. Es el
# unico punto del diseno que no se negocia, y hay pruebas que lo sostienen.
PALETA = {
    "fondo_profundo": "#0A0A0F",   # casi negro, para que el neon respire
    "superficie": "#0F0F16",       # apenas mas claro; se usa poco a proposito
    "superficie_alta": "#1A1A24",  # lineas separadoras y pistas de los sliders
    "turquesa": "#4FF0DC",         # acento principal
    "rosa": "#FF5FA2",             # acento secundario
    "texto_claro": "#EDEDF2",
    "texto_tenue": "#585868",
}

# Relleno de cada estado: apagado, para que la figura tenga cuerpo sin apagar el borde.
COLOR_POR_ESTADO = {
    "ESCUCHANDO": "#12403C",    # turquesa profundo
    "PENSANDO": "#1B2E5C",      # azul profundo
    "RESPONDIENDO": "#4A1733",  # rosa profundo
    "ATENCION": "#4A3312",      # ambar profundo
}

# Borde luminoso: es el que lleva la senal. Sobre un fondo casi negro, el relleno
# apagado solo no comunica nada; el borde si.
COLOR_BORDE_POR_ESTADO = {
    "ESCUCHANDO": "#4FF0DC",    # turquesa neon
    "PENSANDO": "#7FA8FF",      # azul claro
    "RESPONDIENDO": "#FF5FA2",  # rosa neon
    "ATENCION": "#FFC24D",      # ambar
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

# ALTERNO CAMBIADO EL 2026-08-23. El anterior, Qwen2.5-7B-Instruct-Turbo, funcionaba
# el 14 de agosto y para el 17 devolvia HTTP 503 en todos los intentos: Together lo
# retiro en esos tres dias. Se detecto usando el selector de la ventana.
#
# Se probaron los 169 modelos de chat del catalogo uno por uno. Solo 20 responden. De
# esos, en espanol y con este system prompt:
#     Qwen/Qwen3.5-9B                         12 s, 1300 tokens  -> inservible para voz
#     openai/gpt-oss-20b                      1.7 s, 170 tokens  -> aceptable
#     meta-llama/Llama-3.3-70B-Instruct-Turbo 1.5 s,  65 tokens  -> elegido
#
# El elegido es ademas el que el diseno original pedia: la seccion 4 del spec proponia
# un selector Qwen / Llama, y se descarto en T-07 porque entonces Llama no respondia.
# Ahora si, asi que el selector recupera su intencion: dos FAMILIAS distintas de modelo,
# no dos tamanos de la misma. Para la sustentacion es mejor comparacion.
#
# NOTA: el campo `running` del catalogo esta en false para los 169. No sirve para saber
# que modelo esta vivo. La unica forma sigue siendo pedirle algo y ver si contesta.
MODELO_LLM_ALTERNO = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

# Precio por millon de tokens en Together, consultado el 2026-08-14. Se anota aqui
# porque el saldo es limitado y conviene saber que cuesta cada turno.
#   Qwen3.8-2.4T-A95B              entrada $2.50   salida $6.25
#   Llama-3.3-70B-Instruct-Turbo   entrada $1.04   salida $1.04
#   whisper-large-v3               $0.0015 por minuto de audio
# Precios releidos del catalogo el 2026-08-23, no copiados de la web.

MODELO_STT = "openai/whisper-large-v3"
IDIOMA_STT = "es"

# --- Identidad del asistente ------------------------------------------------
#
# El PROYECTO se llama Mini-JARVIS: es el nombre de la tarea y asi se queda en el
# repositorio, el informe y la sustentacion. La ASISTENTE se llama Elena, que es a
# quien se le habla.
#
# La seccion 4 del enunciado lo permite explicitamente: "la personalidad del asistente
# (nombre, tono, estilo de respuesta) queda a criterio de cada equipo: puede ser una
# replica cercana a JARVIS o una identidad propia, siempre que quede definida mediante
# un system prompt claro y documentado".
#
# El nombre vive AQUI y no escrito a mano en cada archivo. Si manana se cambia, se
# cambia en un sitio: la ventana, el saludo, el system prompt de la nube y el del
# modelo local lo leen todos de esta constante.
NOMBRE_ASISTENTE = "Elena"

# Voz elegida el 2026-08-23 escuchando ocho muestras de la misma frase.
# Es argentina y se llama Elena, igual que la asistente: el nombre y la voz van juntos.
# Antes fueron es-MX-DaliaNeural y es-ES-XimenaNeural.
VOZ_TTS = "es-AR-ElenaNeural"

# Tono y ritmo: NEUTROS, y es una decision, no un descuido.
#
# Estas dos constantes existieron desde el 2026-08-14 con valores "+35Hz" y "+8%" y un
# comentario que decia que la voz estaba ajustada, pero **ningun archivo las leia**:
# eran dos constantes muertas afirmando un ajuste inexistente. Se conectaron de verdad
# en core/tts_engine.py, y una vez conectadas se ponen a cero, porque se eligieron
# las muestras SIN retoque. Se dejan declaradas porque el motor ya las respeta.
TONO_TTS = "+0Hz"
RITMO_TTS = "+0%"


# --- Captura de audio (correccion del 2026-08-14) ---------------------------
# Whisper ALUCINA con audio vacio: ante silencio devuelve muletillas como "Gracias" o
# "Subtitulos realizados por...". Se detecto pulsando y soltando sin hablar.
# La defensa es no enviarle nada que no tenga voz dentro: se exige una duracion minima
# y un volumen minimo. De paso ahorra dinero, porque cada envio se paga.
DURACION_MINIMA_GRABACION = 0.35  # segundos

# Volumen medio (RMS) por debajo del cual se considera que no se hablo. Las muestras
# son enteros de 16 bits (-32768 a 32767); el ruido de fondo de un portatil ronda 30-80
# y la voz normal pasa de 500 con holgura.
UMBRAL_DE_SILENCIO = 180


# --- Interfaz (correccion del 2026-08-14) -----------------------------------
# Cuanto se queda a la vista el estado ATENCION antes de volver a reposo.
#
# Historia de este numero, que ya va por su tercera version:
#   instantaneo -> el estado ocurria durante microsegundos y nadie lo veia jamas.
#   2.5 s       -> medido y correcto, y SEGUIA sin verse (2026-08-23).
#   5.0 s       -> el actual.
#
# La segunda vez se comprobo con el mainloop real que la ventana SI pintaba el
# triangulo durante 2.5 s exactos. El mecanismo estaba bien; lo que fallaba es que el
# mensaje de error aparece en la columna del CENTRO y el indicador esta en la de la
# IZQUIERDA. Quien acaba de hablar mira el texto, no la figura, y para cuando levanta
# la vista ya se fue.
#
# Por eso este numero sube Y ademas el aviso del chat se pinta del mismo ambar que el
# triangulo (ver gui/desktop_app.py). Un aviso que no se alcanza a ver no es un aviso,
# aunque el reloj diga que estuvo ahi.
SEGUNDOS_EN_ATENCION = 5.0


# --- Memoria conversacional (diseno, seccion 8) -----------------------------
# Se conservan los ultimos 10 turnos (usuario + asistente); al superarlos se
# descarta el par mas antiguo.
MAX_TURNOS_MEMORIA = 10


# --- Tool calling (diseno, seccion 7) ---------------------------------------
# Maximo de rondas de tool calling por turno: evita un bucle infinito si el
# modelo insiste en llamar herramientas. Al agotarse, responde con el texto
# que tenga.
LIMITE_RONDAS_TOOL_CALLING = 2

# Lista blanca de dominios para abrir_pagina (diseno, seccion 9). Minusculas,
# sin esquema ni barra final. La fija el Ingeniero: no se amplia ni se reduce
# aqui. La logica de validacion de URL vive en tools/system_skills.py (T-15),
# fuera del alcance de este archivo.
DOMINIOS_PERMITIDOS = frozenset(
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

# Tope del slider de temperatura. NO es un numero elegido a ojo: sale de medir.
#
# Se movio el slider al maximo (1.5) y la aplicacion se quedo pensando y acabo
# diciendo que no habia internet. La conexion estaba perfecta. Midiendo la misma frase
# contra la API real, con el modelo de razonamiento predeterminado:
#
#     temp 0.0   ->    2.4 s        temp 1.35  ->    1.7 s
#     temp 0.7   ->    1.1 s        temp 1.40  ->    0.7 s
#     temp 1.2   ->    1.1 s        temp 1.45  ->    3.0 s
#     temp 1.3   ->    0.9 s        temp 1.50  ->  152 s / 102 s / 102 s / 1.3 s
#
# A partir de 1.5 el servidor se atasca unos 100 segundos en dos de cada tres
# intentos. No devuelve mas texto -de hecho devolvio menos-, simplemente tarda. Por
# debajo de 1.45 no ocurre nunca.
#
# Un control que la usuaria puede mover hasta un valor que rompe la aplicacion no es un
# control, es una trampa. El slider llega hasta 1.4, que sigue siendo territorio de
# sobra para demostrar el efecto en vivo.
TEMPERATURA_MAXIMA = 1.4
