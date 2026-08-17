"""
exploration/transformer_lab.py

Modulo de exploracion del Transformer para Mini-JARVIS (tarea T-11).

Por que existe este archivo: los LLM de produccion del proyecto corren en los
servidores de Together AI, detras de un endpoint HTTP. Un endpoint HTTP solo devuelve
texto: es fisicamente imposible pedirle las matrices internas de self-attention a un
modelo que no esta cargado en nuestra propia memoria. Por eso este laboratorio se hace
en dos niveles, tal como describe la seccion 10 del documento de diseno
(docs/specs/2026-08-13-mini-jarvis-design.md):

  Nivel 1 - Se descarga SOLO el tokenizador real de Qwen2.5 (pocos MB, sin pesos del
            modelo, sin GPU) para mostrar como el texto se convierte en tokens e IDs.

            Se usa el de Qwen y no el de Llama por dos razones concretas. Primera:
            Qwen2.5-7B-Instruct-Turbo es uno de los dos modelos que el proyecto usa
            de verdad (el alterno del selector de la GUI), asi que este es su
            tokenizador real, no un sustituto didactico. Segunda: el repositorio del
            tokenizador de Llama 3.3 en Hugging Face esta restringido — exige una
            cuenta con la licencia de Meta aceptada — y una demostracion que depende
            de un permiso ajeno es una demostracion fragil. El tokenizador de Qwen2.5
            es publico y ademas es el mismo para todos los tamanos de la familia.
  Nivel 2 - Se usa un Transformer pequeno que si corre completo en esta maquina,
            BETO (dccuchile/bert-base-spanish-wwm-cased, ~110M parametros, entrenado
            en espanol), para extraer de verdad los embeddings y las matrices de
            self-attention y dibujar un mapa de calor.

Se ejecuta de forma independiente del resto del proyecto:

    python -m exploration.transformer_lab

No importa config.py ni nada de core/, no abre GUI, no usa microfono ni ninguna API
de pago: todo corre localmente con modelos de Hugging Face.

LA TRAMPA CRITICA (verificada experimentalmente durante T-01): a partir de
transformers 5.x, el backend de atencion por defecto es SDPA (scaled dot product
attention de PyTorch). SDPA no calcula ni expone las matrices de atencion intermedias:
si se pide output_attentions=True con SDPA, el resultado es que `salida.attentions`
llega como None, y esto ocurre EN SILENCIO, sin lanzar ninguna excepcion. El script
"corre bien" y no cumple su objetivo. La correccion obligatoria es cargar el modelo
con attn_implementation="eager", que es el backend clasico que si materializa esas
matrices. Ademas, mas abajo (ver _verificar_atenciones) el script comprueba esto en
tiempo de ejecucion y revienta con un mensaje explicito si algo sale mal, en vez de
dejar pasar unas atenciones vacias como si nada.
"""

import sys
from pathlib import Path

# Obligatorio: fijar el backend "Agg" (sin ventana) ANTES de importar pyplot.
# Este script no abre ninguna interfaz grafica; solo escribe un archivo PNG en disco.
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (import intencionalmente despues de matplotlib.use)
import numpy as np  # noqa: E402
import torch  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from transformers import AutoModel, AutoTokenizer  # noqa: E402
from transformers import logging as hf_logging  # noqa: E402

# Silenciamos SOLO el ruido informativo de la libreria transformers: la barra de
# progreso "Loading weights" y el reporte de pesos UNEXPECTED/MISSING que imprime al
# cargar BETO con AutoModel (es esperado: BETO se publico como checkpoint de
# BertForPreTraining y AutoModel solo carga el encoder, nunca la cabeza de
# prediccion de palabras enmascaradas ni el pooler). No se sube el umbral por encima
# de "error": una excepcion real durante la carga sigue interrumpiendo el script con
# su traceback normal; esto no oculta fallos, solo aviso informativo repetitivo.
hf_logging.set_verbosity_error()
hf_logging.disable_progress_bar()


# ---------------------------------------------------------------------------------
# Constantes del laboratorio
# ---------------------------------------------------------------------------------

# Nivel 1: el tokenizador real de uno de los LLM del proyecto (sin sus pesos).
# Together sirve este modelo como "Qwen/Qwen2.5-7B-Instruct-Turbo"; el sufijo Turbo
# es el nombre de su despliegue cuantizado, no otro tokenizador. En Hugging Face el
# repositorio se llama sin ese sufijo, y es de donde se descarga aqui.
NOMBRE_TOKENIZADOR_QWEN = "Qwen/Qwen2.5-7B-Instruct"

# Nivel 2: el Transformer pequeno y local sobre el que si podemos mirar "por dentro".
NOMBRE_MODELO_BETO = "dccuchile/bert-base-spanish-wwm-cased"

# Frase de ejemplo para el nivel 1. Es una frase propia del proyecto (habla de
# Mini-JARVIS y de la bateria del portatil) y se dejo CON acentos a proposito: los
# caracteres acentuados son justo los que mas se fragmentan en sub-tokens raros, y eso
# es pedagogicamente valioso para la sustentacion oral.
FRASE_NIVEL_1 = (
    "Mini-JARVIS es mi asistente de voz y me avisa cuando la batería "
    "del portátil está por agotarse."
)

# Frase de ejemplo para el nivel 2. Se ajusto (probando varias variantes naturales en
# espanol, todas del dominio "asistente de voz") hasta que el tokenizador de BETO
# produce EXACTAMENTE 18 sub-tokens; sumando [CLS] y [SEP] da 20 tokens, que es la
# forma verificada durante T-01 para las capas de embeddings y de atencion. Se
# comprueba en tiempo de ejecucion con una asercion, no se da por sentado.
FRASE_NIVEL_2 = (
    "El asistente escucha mi voz, piensa la respuesta y habla antes "
    "de quedarse sin bateria."
)
TOKENS_ESPERADOS_NIVEL_2 = 20

# Capa y cabeza de atencion elegidas para el mapa de calor. Se probaron las 12 capas
# por 12 cabezas (144 combinaciones) midiendo cuanta atencion pone cada una en
# palabras de contenido en vez de en los tokens especiales [CLS]/[SEP]. La capa 5
# (humana: capa 6), cabeza 3 (humana: cabeza 4) resulto ser una "cabeza de token
# anterior": cada fila ilumina casi en exclusiva la columna inmediatamente a su
# izquierda, es decir, cada token le presta casi toda su atencion a la palabra que
# lo precede. Es un patron clasico y muy documentado en modelos tipo BERT, y es
# facil de senalar en la imagen durante la sustentacion oral.
CAPA_ELEGIDA_BASE0 = 5
CABEZA_ELEGIDA_BASE0 = 3

# Paleta del proyecto tras el rediseno T-19 (2026-08-17): tema oscuro, turquesa y
# rosa. El mapa se muestra dentro de la ventana, asi que si se quedara con el fondo
# crema del tema anterior apareceria como un rectangulo blanco en medio de una
# interfaz oscura. Los valores se repiten aqui en vez de importarlos de config.py a
# proposito: este modulo corre solo, sin `.env` ni credenciales, y esa independencia
# es un criterio de aceptacion de T-11.
COLOR_FONDO = "#101F27"      # fondo profundo
COLOR_SUPERFICIE = "#18303B"
COLOR_TURQUESA = "#39C5BB"
COLOR_ROSA = "#FF6B9D"
COLOR_TEXTO = "#E8F6F5"      # texto claro sobre fondo oscuro

NOMBRE_PNG_SALIDA = "mapa_atencion.png"


# ---------------------------------------------------------------------------------
# Utilidades de presentacion (la salida de consola es parte del entregable: se
# proyecta y se lee en voz alta durante la sustentacion oral).
# ---------------------------------------------------------------------------------

def _encabezado(texto):
    linea = "=" * 78
    print("\n" + linea)
    print(texto)
    print(linea)


def _subtitulo(texto):
    print("\n--- " + texto + " ---")


def _cargar_o_fallar(descripcion, funcion, *args, **kwargs):
    """Envuelve una descarga de Hugging Face y explica en espanol un fallo de red.

    Concepto: la primera vez que se pide un modelo o un tokenizador, la libreria
    transformers lo descarga de los servidores de Hugging Face y lo guarda en una
    cache local (normalmente en el directorio del usuario). Si no hay conexion a
    internet en ese primer intento, la descarga falla. En ejecuciones posteriores,
    con la cache ya poblada, el script funciona sin conexion.
    """
    try:
        return funcion(*args, **kwargs)
    except Exception as excepcion:  # noqa: BLE001 - fallo de red o de cache, cualquiera se explica igual
        print(f"\n[ERROR] No se pudo cargar {descripcion} desde Hugging Face.")
        print(f"Detalle tecnico: {type(excepcion).__name__}: {excepcion}")
        print(
            "\nEsto casi siempre significa que no hay conexion a internet en este "
            "momento. Este script necesita descargar el tokenizador y/o los pesos del "
            "modelo (unos cientos de MB en el caso de BETO) la PRIMERA vez que se "
            "ejecuta, para poblar la cache local de Hugging Face. Una vez poblada esa "
            "cache, las siguientes ejecuciones funcionan sin necesidad de red. "
            "Verifica tu conexion e intenta de nuevo."
        )
        sys.exit(1)


# ---------------------------------------------------------------------------------
# API reutilizable
#
# Estas funciones son el laboratorio de verdad; lo que viene despues (nivel_1, nivel_2)
# solo las llama y da formato a la consola. Existen porque la pestana Laboratorio de la
# aplicacion (T-13) necesita lo mismo que el script, y tener dos implementaciones del
# mismo calculo es la forma mas segura de que un dia digan cosas distintas: se corrige
# una y se olvida la otra, y la demostracion contradice al informe.
#
# Los modelos se guardan en cache al primer uso: BETO pesa cientos de MB y tarda varios
# segundos en cargar. En el script da igual porque se carga una vez; en la aplicacion
# seria inaceptable esperar eso en cada frase.
# ---------------------------------------------------------------------------------

_cache_modelos = {}


def obtener_tokenizador_qwen():
    """Devuelve el tokenizador de Qwen, cargandolo solo la primera vez."""
    if "qwen" not in _cache_modelos:
        _cache_modelos["qwen"] = _cargar_o_fallar(
            f"el tokenizador de {NOMBRE_TOKENIZADOR_QWEN}",
            AutoTokenizer.from_pretrained,
            NOMBRE_TOKENIZADOR_QWEN,
        )
    return _cache_modelos["qwen"]


def obtener_beto():
    """Devuelve (tokenizador, modelo) de BETO, cargandolos solo la primera vez.

    El modelo se carga con `attn_implementation="eager"` SIEMPRE. Es la trampa
    documentada al inicio del archivo: sin eso, `output_attentions=True` devuelve
    None en silencio y todo el laboratorio queda vacio sin dar ningun error.
    """
    if "beto" not in _cache_modelos:
        tokenizador = _cargar_o_fallar(
            f"el tokenizador de {NOMBRE_MODELO_BETO}",
            AutoTokenizer.from_pretrained,
            NOMBRE_MODELO_BETO,
        )
        modelo = _cargar_o_fallar(
            f"los pesos de {NOMBRE_MODELO_BETO}",
            AutoModel.from_pretrained,
            NOMBRE_MODELO_BETO,
            attn_implementation="eager",
        )
        # Modo inferencia: se desactivan capas como dropout y el resultado es
        # determinista, que es lo que se quiere para poder repetir una demostracion.
        modelo.eval()
        _cache_modelos["beto"] = (tokenizador, modelo)
    return _cache_modelos["beto"]


def token_legible(token):
    """Convierte un token crudo en algo que una persona pueda leer en pantalla.

    El tokenizador de Qwen marca el inicio de palabra con 'Ġ' (un espacio codificado);
    se muestra como punto medio para que se vea donde habia un espacio en el original.
    """
    return "·" + token[1:] if token.startswith("Ġ") else token


def tokenizar_con_qwen(frase):
    """Corta la frase en tokens con el tokenizador real de Qwen.

    Devuelve una lista de (indice, id_numerico, token_legible). Es lo que muestran
    tanto la consola del script como la tabla de la pestana Laboratorio.
    """
    tokenizador = obtener_tokenizador_qwen()
    ids = tokenizador.encode(frase)
    tokens = tokenizador.convert_ids_to_tokens(ids)
    return [
        (indice, id_token, token_legible(token))
        for indice, (token, id_token) in enumerate(zip(tokens, ids))
    ]


def analizar_con_beto(frase):
    """Pasa la frase por BETO y devuelve sus tokens, embeddings y atenciones reales.

    Devuelve un diccionario con:
      tokens              lista de tokens, incluidos [CLS] y [SEP]
      embeddings          tensor (1, n_tokens, 768)
      atenciones          tupla de 12 tensores (1, 12, n_tokens, n_tokens)
      forma_embeddings    la forma de arriba como tupla, para mostrarla
      n_capas, n_cabezas  numero de capas y de cabezas de atencion
    """
    tokenizador, modelo = obtener_beto()
    entradas = tokenizador(frase, return_tensors="pt")
    tokens = tokenizador.convert_ids_to_tokens(entradas["input_ids"][0])

    # Sin torch.no_grad() PyTorch guardaria informacion para calcular gradientes, como
    # si fueramos a entrenar. Aqui solo hay inferencia: es mas rapido y usa menos
    # memoria desactivarlo.
    with torch.no_grad():
        salida = modelo(**entradas, output_attentions=True)

    _verificar_atenciones(salida)

    return {
        "tokens": tokens,
        "embeddings": salida.last_hidden_state,
        "atenciones": salida.attentions,
        "forma_embeddings": tuple(salida.last_hidden_state.shape),
        "n_capas": len(salida.attentions),
        "n_cabezas": salida.attentions[0].shape[1],
    }


# ---------------------------------------------------------------------------------
# Nivel 1 - Tokenizacion
# ---------------------------------------------------------------------------------

def nivel_1_tokenizacion():
    """Muestra como el tokenizador real de Qwen convierte texto en tokens e IDs.

    CONCEPTO CLAVE: un modelo de lenguaje no "lee" palabras como lo hace una persona.
    Antes de que cualquier texto entre a la red neuronal, un componente llamado
    tokenizador lo corta en fragmentos llamados tokens (pueden ser una palabra
    completa, un pedazo de palabra, un signo de puntuacion o incluso un solo
    caracter) y traduce cada token a un numero entero: su ID. El modelo, por dentro,
    unicamente ve una lista de numeros. Ese vocabulario de tokens es fijo y se define
    al entrenar el modelo; una palabra que no aparecio (o aparecio poco) en los datos
    de entrenamiento se parte en varios sub-tokens mas pequenos que si son conocidos.
    """
    _encabezado("NIVEL 1 - TOKENIZACION (tokenizador real de Qwen2.5-Instruct)")
    print(
        "Se descarga UNICAMENTE el tokenizador (un archivo de vocabulario y reglas "
        "de division de texto), sin un solo peso del modelo. Pesa pocos megabytes, "
        "no necesita GPU, y es exactamente el mismo que usa el modelo Qwen que "
        "responde en la aplicacion."
    )

    tokenizador = obtener_tokenizador_qwen()

    _subtitulo("Frase de ejemplo (propia del proyecto Mini-JARVIS)")
    print(f'"{FRASE_NIVEL_1}"')

    # Misma funcion que alimenta la tabla de la pestana Laboratorio de la aplicacion.
    filas = tokenizar_con_qwen(FRASE_NIVEL_1)
    ids = tokenizador.encode(FRASE_NIVEL_1)
    tokens = tokenizador.convert_ids_to_tokens(ids)

    _subtitulo(f"Tokens generados: {len(filas)}")
    print(
        "Cada fila de abajo es un token con su ID numerico. El caracter 'Ġ' que "
        "aparece pegado a algunos tokens es la forma en que este tokenizador marca "
        "'aqui empezaba un espacio en el texto original'; se muestra como un punto "
        "medio (·) para que se lea con claridad."
    )
    print(
        "AVISO PARA LA SUSTENTACION: mas abajo veras tokens con aspecto de error de "
        "codificacion, como 'ÃŃa' donde el texto decia 'ía'. NO es un error del "
        "programa. Este tokenizador es de tipo byte-level BPE: no trabaja sobre "
        "letras sino sobre los BYTES del texto en UTF-8, y una letra acentuada ocupa "
        "dos bytes. Al mostrar cada byte como si fuera un caracter suelto aparecen "
        "esos simbolos raros. Es la representacion interna real del modelo, y es "
        "justamente por eso que las palabras acentuadas se parten en mas sub-tokens "
        "que las palabras sin acento."
    )
    print(f"{'idx':>4}  {'ID token':>9}  token")
    print(f"{'-' * 4}  {'-' * 9}  {'-' * 30}")
    for indice, id_token, token_visible in filas:
        print(f"{indice:>4}  {id_token:>9}  {token_visible}")

    # Concepto: agrupamos los tokens en "palabras" para mostrar donde el
    # tokenizador tuvo que partir una palabra en varios pedazos. Un token que NO
    # empieza con 'Ġ' (y que no es el primero de la frase) es, por definicion, la
    # continuacion de la palabra anterior: no hubo espacio antes de el.
    grupos = []
    for token in tokens:
        es_inicio_de_palabra = token.startswith("Ġ") or len(grupos) == 0
        if es_inicio_de_palabra:
            grupos.append([token])
        else:
            grupos[-1].append(token)

    _subtitulo("Palabras que se partieron en varios sub-tokens")
    print(
        "Este es exactamente el fenomeno que se explicara en la sustentacion oral: "
        "las palabras acentuadas y los nombres poco frecuentes (como 'Mini-JARVIS', "
        "que no existe en el vocabulario de entrenamiento) no tienen un token propio, "
        "asi que el tokenizador los reconstruye pegando varios sub-tokens mas chicos."
    )
    hubo_alguna = False
    for grupo in grupos:
        if len(grupo) > 1:
            hubo_alguna = True
            palabra_reconstruida = tokenizador.convert_tokens_to_string(grupo).strip()
            print(f"  '{palabra_reconstruida}' -> {len(grupo)} sub-tokens: {grupo}")
    if not hubo_alguna:
        print("  (en esta frase, ninguna palabra se partio en mas de un sub-token)")


# ---------------------------------------------------------------------------------
# Nivel 2 - Embeddings y self-attention
# ---------------------------------------------------------------------------------

def _verificar_atenciones(salida):
    """Comprueba en tiempo de ejecucion que salida.attentions realmente trae datos.

    Esta funcion existe por la trampa critica documentada al inicio del archivo:
    con el backend SDPA (el que usa transformers 5.x por defecto), pedir
    output_attentions=True devuelve None SIN lanzar ninguna excepcion. El script no
    puede "pasar" silenciosamente con atenciones vacias: si esto llega a ocurrir
    (por ejemplo si alguien quita accidentalmente attn_implementation="eager"),
    preferimos reventar aqui con un mensaje que explique la causa exacta, en vez de
    seguir adelante como si todo estuviera bien.
    """
    if salida.attentions is None or len(salida.attentions) == 0:
        raise RuntimeError(
            "salida.attentions llego vacio (None). Causa exacta: transformers 5.x usa "
            "por defecto el backend de atencion SDPA (scaled dot product attention de "
            "PyTorch), que NO materializa las matrices de atencion intermedias aunque "
            "se pida output_attentions=True; el resultado es None y no se lanza ninguna "
            "excepcion, por lo que el fallo es silencioso. La correccion es cargar el "
            "modelo con AutoModel.from_pretrained(nombre, attn_implementation='eager')."
        )


def nivel_2_embeddings_y_atencion():
    """Extrae embeddings y matrices de self-attention reales de BETO.

    CONCEPTO CLAVE (embeddings): un embedding es una lista de numeros (un vector) que
    representa el significado de un token DENTRO de su contexto, es decir, tomando en
    cuenta las palabras que lo rodean. BETO representa cada token con 768 numeros. No
    hay una etiqueta humana para lo que significa cada uno de esos 768 numeros por
    separado; lo que importa es que tokens con significados o usos parecidos terminan
    con vectores parecidos entre si, en un espacio de 768 dimensiones que el modelo
    aprendio durante su entrenamiento.

    CONCEPTO CLAVE (self-attention): es el mecanismo que le permite a cada token
    "mirar" a todos los demas tokens de la misma frase (incluido el mismo) y decidir
    cuanto peso ponerle a cada uno para construir su propio embedding contextual. Ese
    reparto de peso es una distribucion de probabilidad (una funcion softmax): por eso
    cada fila de la matriz de atencion siempre suma exactamente 1.0.
    """
    _encabezado("NIVEL 2 - EMBEDDINGS Y SELF-ATTENTION (BETO, local y completo)")
    print(
        f"Modelo: {NOMBRE_MODELO_BETO} (~110 millones de parametros, entrenado en "
        "espanol). A diferencia del nivel 1, aqui SI se descargan y se ejecutan los "
        "pesos completos del modelo, porque necesitamos mirar dentro de sus capas."
    )

    tokenizador, _modelo = obtener_beto()

    _subtitulo("Frase de ejemplo (propia del proyecto Mini-JARVIS)")
    print(f'"{FRASE_NIVEL_2}"')

    n_subtokens = len(tokenizador.tokenize(FRASE_NIVEL_2))
    n_tokens_totales = n_subtokens + 2  # +2 por [CLS] y [SEP]
    print(
        f"Sub-tokens de la frase: {n_subtokens}  ->  + [CLS] y [SEP]  =  "
        f"{n_tokens_totales} tokens totales."
    )
    if n_tokens_totales != TOKENS_ESPERADOS_NIVEL_2:
        print(
            f"[AVISO] Se esperaban {TOKENS_ESPERADOS_NIVEL_2} tokens y se obtuvieron "
            f"{n_tokens_totales}. Se continua con la forma real (no se fuerza una "
            "frase artificial): las explicaciones de las dimensiones de abajo usan "
            "el numero real de tokens de esta ejecucion."
        )

    # Mismo analisis que usa la pestana Laboratorio: una sola implementacion.
    analisis = analizar_con_beto(FRASE_NIVEL_2)
    tokens = analisis["tokens"]

    _subtitulo("Tokens de BETO para esta frase (incluye [CLS] y [SEP])")
    print(
        "El prefijo '##' marca un sub-token que continua la palabra anterior sin "
        "espacio: es la misma idea del nivel 1, con otra notacion."
    )
    for indice, token in enumerate(tokens):
        print(f"  {indice:>2}  {token}")

    embeddings = analisis["embeddings"]
    _subtitulo("Embeddings contextuales (last_hidden_state)")
    print(f"Forma del tensor: {tuple(embeddings.shape)}")
    print(
        f"  - Dimension 1 ({embeddings.shape[0]}): tamano del lote. Aqui procesamos "
        "una sola frase a la vez, asi que vale 1."
    )
    print(
        f"  - Dimension 2 ({embeddings.shape[1]}): numero de tokens de la frase "
        "(incluyendo [CLS] y [SEP])."
    )
    print(
        f"  - Dimension 3 ({embeddings.shape[2]}): tamano del vector de significado "
        "de CADA token en el espacio semantico interno de BETO. Son 768 numeros que, "
        "juntos, codifican el significado contextual de ese token."
    )

    atenciones = analisis["atenciones"]
    _subtitulo("Matrices de self-attention")
    print(f"Numero de capas de atencion devueltas: {len(atenciones)} (BETO tiene 12 capas Transformer).")
    forma_capa = tuple(atenciones[0].shape)
    print(f"Forma de UNA capa de atencion: {forma_capa}")
    print(
        f"  - Dimension 1 ({forma_capa[0]}): tamano del lote (una sola frase)."
    )
    print(
        f"  - Dimension 2 ({forma_capa[1]}): numero de cabezas de atencion de esa "
        "capa. BETO calcula 12 'formas de mirar' distintas en paralelo dentro de cada "
        "capa, cada una puede aprender a fijarse en un tipo de relacion diferente."
    )
    print(
        f"  - Dimension 3 ({forma_capa[2]}): token que CONSULTA (query) - la fila: "
        "'desde este token, cuanto miro a los demas'."
    )
    print(
        f"  - Dimension 4 ({forma_capa[3]}): token CONSULTADO (key) - la columna: "
        "'a este otro token, cuanto lo miro'."
    )

    _subtitulo("Verificacion: cada fila de atencion suma 1.0")
    fila = atenciones[0][0, 0, 1]  # capa 0, cabeza 0, token consultante 1 (la primera palabra real)
    suma_fila = fila.sum()
    print(
        f"Fila elegida: capa 0, cabeza 0, token consultante = '{tokens[1]}' (indice 1)."
    )
    print(f"Suma de esa fila: {suma_fila.item():.6f}")
    es_uno = torch.allclose(suma_fila, torch.tensor(1.0), atol=1e-4)
    print(f"torch.allclose(suma, 1.0) = {es_uno}")
    print(
        "Por que suma 1.0: cada fila de la matriz de atencion es el resultado de una "
        "funcion softmax. El softmax convierte una lista de puntajes en una "
        "distribucion de probabilidad: numeros entre 0 y 1 que siempre suman "
        "exactamente 1. En este caso representa 'que porcentaje de mi atencion total "
        "reparto entre cada uno de los demas tokens de la frase' — nunca mas, nunca "
        "menos que el 100 %."
    )
    if not es_uno:
        raise RuntimeError(
            "La fila de atencion verificada no suma 1.0 dentro de la tolerancia "
            "esperada; esto indicaria un problema serio en la extraccion de atenciones."
        )

    return tokens, atenciones


# ---------------------------------------------------------------------------------
# Mapa de calor
# ---------------------------------------------------------------------------------

def dibujar_mapa_de_atencion(tokens, atenciones, capa_base0, cabeza_base0,
                             ruta_salida=None, silencioso=False):
    """Dibuja y guarda un mapa de calor de una capa y cabeza de atencion concretas.

    CONCEPTO CLAVE: un mapa de calor de atencion es, literalmente, la matriz que
    describe el nivel 2 vuelta imagen. Cada celda (fila=token que consulta,
    columna=token consultado) se pinta con un color segun cuanta atencion le puso
    ese token a ese otro token; entre mas oscuro/saturado, mas atencion.

    `ruta_salida` y `silencioso` existen para la pestana Laboratorio de la aplicacion
    (T-13), que necesita el PNG en otro sitio y sin imprimir nada por consola. El
    dibujo es exactamente el mismo, y esa es la idea: la imagen que se ve en la
    aplicacion y la del informe salen del mismo codigo. Devuelve la ruta escrita.
    """
    # En modo silencioso los comentarios de consola se descartan. Se usa un nombre
    # propio en vez de sombrear `print`: sombrearlo volveria local ese nombre en toda
    # la funcion y reventaria en el camino normal.
    escribir = (lambda *_a, **_k: None) if silencioso else print

    if not silencioso:
        _encabezado("MAPA DE CALOR DE ATENCION")

    capa_humana = capa_base0 + 1
    cabeza_humana = cabeza_base0 + 1
    escribir(
        f"Capa elegida: indice base-0 = {capa_base0}  (capa humana #{capa_humana} de 12)"
    )
    escribir(
        f"Cabeza elegida: indice base-0 = {cabeza_base0}  (cabeza humana #{cabeza_humana} de 12)"
    )
    escribir(
        "Se eligio esta combinacion porque, de las 144 capas x cabezas posibles, es "
        "una 'cabeza de token anterior': en el mapa se ve una franja iluminada justo "
        "a la izquierda de la diagonal principal, es decir, cada token le presta casi "
        "toda su atencion a la palabra que lo precede inmediatamente. Es un patron "
        "clasico y muy documentado en modelos tipo BERT, y resulta facil de senalar "
        "en la imagen durante la sustentacion oral."
    )

    matriz = atenciones[capa_base0][0, cabeza_base0].numpy()  # (n_tokens, n_tokens)

    # Colormap continuo con los colores del tema: va del fondo oscuro (atencion casi
    # nula) al turquesa y de ahi al rosa vivo (atencion maxima). Se eligio que el
    # valor alto sea el mas luminoso porque sobre fondo oscuro la vista busca la luz:
    # las celdas que importan son las que brillan, y la franja de la diagonal se
    # senala sola en un proyector.
    mapa_de_color = LinearSegmentedColormap.from_list(
        "mini_jarvis_atencion",
        [COLOR_FONDO, COLOR_SUPERFICIE, COLOR_TURQUESA, COLOR_ROSA],
    )

    figura, ejes = plt.subplots(figsize=(10.5, 9))
    figura.patch.set_facecolor(COLOR_FONDO)
    ejes.set_facecolor(COLOR_FONDO)

    imagen = ejes.imshow(matriz, cmap=mapa_de_color, vmin=0.0, vmax=float(matriz.max()))

    n_tokens = len(tokens)
    ejes.set_xticks(np.arange(n_tokens))
    ejes.set_yticks(np.arange(n_tokens))
    ejes.set_xticklabels(tokens, rotation=45, ha="right", color=COLOR_TEXTO, fontsize=9)
    ejes.set_yticklabels(tokens, color=COLOR_TEXTO, fontsize=9)

    ejes.set_xlabel("Token consultado (key)", color=COLOR_TEXTO, fontsize=11)
    ejes.set_ylabel("Token que consulta (query)", color=COLOR_TEXTO, fontsize=11)
    ejes.set_title(
        f"Mapa de atencion — {NOMBRE_MODELO_BETO}\n"
        f"Capa {capa_humana} de 12, cabeza {cabeza_humana} de 12",
        color=COLOR_TEXTO,
        fontsize=12,
        pad=14,
    )

    for spine in ejes.spines.values():
        spine.set_edgecolor(COLOR_TEXTO)

    barra = figura.colorbar(imagen, ax=ejes, fraction=0.046, pad=0.04)
    barra.set_label("Peso de atencion", color=COLOR_TEXTO)
    barra.ax.yaxis.set_tick_params(color=COLOR_TEXTO)
    plt.setp(plt.getp(barra.ax.axes, "yticklabels"), color=COLOR_TEXTO)

    figura.tight_layout()

    if ruta_salida is None:
        ruta_salida = Path(__file__).resolve().parent / NOMBRE_PNG_SALIDA
    ruta_salida = Path(ruta_salida)
    figura.savefig(ruta_salida, dpi=150, facecolor=figura.get_facecolor())
    plt.close(figura)

    escribir(f"\nPNG guardado en: {ruta_salida}")
    escribir(f"Tamano del archivo: {ruta_salida.stat().st_size} bytes")
    return ruta_salida


# ---------------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------------

def main():
    # Primera linea ejecutable: reconfigura la salida estandar a UTF-8. Sin esto, los
    # acentos y caracteres especiales de este script pueden romper la salida cuando
    # la consola de Windows usa una codificacion heredada o cuando la salida se
    # redirige a un archivo o a una tuberia.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    _encabezado("MINI-JARVIS - LABORATORIO DE EXPLORACION DEL TRANSFORMER (T-11)")
    print(
        "Este script no es parte del pipeline de voz de Mini-JARVIS: es un modulo "
        "independiente para demostrar, con un Transformer real corriendo en esta "
        "misma maquina, los tres conceptos que la rubrica exige poder explicar: "
        "tokenizacion, embeddings y self-attention."
    )

    nivel_1_tokenizacion()
    tokens, atenciones = nivel_2_embeddings_y_atencion()
    dibujar_mapa_de_atencion(tokens, atenciones, CAPA_ELEGIDA_BASE0, CABEZA_ELEGIDA_BASE0)

    _encabezado("FIN DEL LABORATORIO")
    print("Los tres pilares del Transformer quedaron demostrados sobre modelos reales:")
    print("  1) Tokenizacion  -> tokenizador real de Qwen2.5-Instruct.")
    print("  2) Embeddings    -> last_hidden_state de BETO, forma (1, N, 768).")
    print("  3) Self-attention -> 12 capas de atencion de BETO, filas que suman 1.0.")


if __name__ == "__main__":
    main()
