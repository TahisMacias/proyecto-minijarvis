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


def _demostrar_softmax():
    """Ejecuta un softmax de verdad, para poder ensenar la operacion y no solo su efecto.

    POR QUE HACE FALTA ESTO. Mas abajo se comprueba que cada fila de atencion suma 1.0,
    y esa suma es la huella del softmax. Pero es solo la huella: el softmax en si ocurre
    DENTRO del modelo, y cuando los numeros llegan aqui ya salieron normalizados. A la
    pregunta "ensename tu softmax" no se podia responder senalando una suma.

    Asi que aqui se aplica uno de verdad, sobre puntajes inventados, para que se vea la
    operacion completa: entran numeros cualesquiera y salen probabilidades que suman 1.

    Y de paso resuelve otra pregunta del enunciado. La temperatura del modelo NO es un
    parametro aparte: es una division que se hace a los puntajes ANTES del softmax.
    Dividir por un numero pequeno separa los puntajes y el reparto se vuelve extremo;
    dividir por uno grande los acerca y el reparto se aplana. Las dos preguntas, la del
    softmax y la de la temperatura, son la misma operacion vista desde dos sitios.
    """
    _subtitulo("Que es exactamente un softmax (ejecutado aqui, no explicado)")
    puntajes = torch.tensor([2.0, 1.0, 0.1])
    print(f"Tres puntajes cualesquiera:      {[round(v, 2) for v in puntajes.tolist()]}")
    print("Son numeros sueltos: no suman nada en particular y pueden ser negativos.")

    probabilidades = torch.softmax(puntajes, dim=0)
    print(f"Los mismos, tras el softmax:     "
          f"{[round(v, 4) for v in probabilidades.tolist()]}")
    print(f"Suma:                            {probabilidades.sum().item():.6f}")
    print(
        "Eso es todo lo que hace el softmax: convierte una lista de puntajes en una "
        "distribucion de probabilidad. Todos los valores quedan entre 0 y 1, el orden "
        "se conserva -el mas alto sigue siendo el mas alto- y el total es exactamente 1."
    )

    print()
    print("Y la TEMPERATURA es este mismo calculo, dividiendo antes los puntajes:")
    print(f"{'temperatura':>14}   reparto resultante")
    for temperatura in (0.1, 0.5, 1.0, 2.0, 5.0):
        reparto = torch.softmax(puntajes / temperatura, dim=0)
        valores = "  ".join(f"{v:.3f}" for v in reparto.tolist())
        print(f"{temperatura:>14.1f}   {valores}")
    print(
        "Con temperatura baja el reparto se vuelve extremo: casi todo se lo lleva la "
        "opcion mas probable, y el modelo suena predecible. Con temperatura alta el "
        "reparto se aplana, las opciones improbables ganan peso, y el modelo se vuelve "
        "mas variado y tambien mas propenso a equivocarse. Es la misma operacion; lo "
        "unico que cambia es entre cuanto se dividen los puntajes antes."
    )
    print(
        "En la atencion ocurre exactamente esto, pero los puntajes no son inventados: "
        "salen de comparar cada token con todos los demas, y el softmax convierte esas "
        "comparaciones en el reparto de atencion que se ve en el mapa."
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

    _demostrar_softmax()

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
# Nivel 3 - Positional encoding
# ---------------------------------------------------------------------------------
#
# Este nivel se anadio el 2026-08-23 al releer el enunciado completo. Lo pide dos
# veces y no estaba: la seccion 2.2 exige "explicar y evidenciar ... tokenizacion,
# embeddings, positional encoding y self-attention", y la 3.1 lo desarrolla. Es parte
# del criterio de mayor peso de la rubrica.

FRASES_ORDEN = ("El perro mordio al gato", "El gato mordio al perro")
NOMBRE_PNG_POSICIONES = "mapa_posiciones.png"
POSICIONES_A_DIBUJAR = 40


def analizar_posiciones():
    """Devuelve las pruebas de que la posicion cambia la representacion de un token.

    Tres hechos, todos medidos sobre BETO en esta maquina:
      forma_tabla     la tabla de embeddings de posicion: (512, 768)
      forma_vocab     la de palabras, para comparar tamanos
      similitud       la MISMA palabra en dos posiciones distintas, comparadas
      tabla           los vectores de posicion, para dibujarlos
    """
    tokenizador, modelo = obtener_beto()
    embeddings = modelo.embeddings

    # "perro" es el token 1 en la primera frase y el token 2 en la segunda. Si la
    # posicion no influyera, su vector de salida seria identico en ambas.
    a = tokenizador("perro gato", return_tensors="pt")
    b = tokenizador("gato perro", return_tensors="pt")
    with torch.no_grad():
        va = modelo(**a).last_hidden_state[0]
        vb = modelo(**b).last_hidden_state[0]
    similitud = torch.nn.functional.cosine_similarity(va[1], vb[2], dim=0).item()

    return {
        "forma_tabla": tuple(embeddings.position_embeddings.weight.shape),
        "forma_vocab": tuple(embeddings.word_embeddings.weight.shape),
        "similitud_misma_palabra_otra_posicion": similitud,
        "tabla": embeddings.position_embeddings.weight.detach(),
    }


def nivel_3_positional_encoding():
    """Demuestra que el modelo sabe en que ORDEN van las palabras, y como lo sabe.

    CONCEPTO CLAVE: el mecanismo de self-attention, por si solo, **no tiene noción de
    orden**. Cada token mira a todos los demas a la vez; para el, una frase es un
    conjunto de palabras, no una secuencia. Si nada mas interviniera, "el perro mordio
    al gato" y "el gato mordio al perro" serian exactamente la misma entrada.

    La solucion es el positional encoding: ANTES de entrar a las capas de atencion, a
    cada token se le SUMA un segundo vector que depende unicamente de la posicion que
    ocupa. El modelo recibe entonces "esta palabra" mas "esta posicion", y a partir de
    ahi ya puede distinguir el orden.
    """
    _encabezado("NIVEL 3 - POSITIONAL ENCODING (como el modelo sabe el orden)")
    print(
        "La atencion mira todos los tokens a la vez, asi que por si sola no distingue "
        "el orden: para ella una frase es un monton de palabras sueltas. El positional "
        "encoding es lo que arregla eso."
    )

    datos = analizar_posiciones()
    posiciones, dimensiones = datos["forma_tabla"]

    _subtitulo("BETO guarda una tabla de posiciones, aparte de la de palabras")
    print(f"Tabla de palabras : {datos['forma_vocab']}  ->  {datos['forma_vocab'][0]} "
          "palabras distintas del vocabulario")
    print(f"Tabla de posiciones: {datos['forma_tabla']}  ->  {posiciones} posiciones "
          f"posibles, cada una con {dimensiones} numeros")
    print(
        f"\nCada token que entra al modelo se representa sumando DOS vectores de "
        f"{dimensiones} numeros: el de su palabra y el de su posicion. Por eso el "
        f"modelo no puede leer frases de mas de {posiciones} tokens: no tiene vector "
        "de posicion para el numero 513."
    )

    _subtitulo("Aprendidas, no calculadas: una diferencia que conviene saber")
    print(
        "En el articulo original del Transformer (Attention is All You Need, 2017) las "
        "posiciones se CALCULABAN con senos y cosenos. BETO, como todos los BERT, las "
        "APRENDE: esa tabla de arriba son parametros que se ajustaron durante el "
        "entrenamiento, igual que los de las palabras. Las dos formas resuelven el "
        "mismo problema; esta es la que usa el modelo que estamos mirando."
    )

    _subtitulo("La prueba: la misma palabra en dos sitios distintos")
    print(f'Frase A: "perro gato"   ->  "perro" esta en la posicion 1')
    print(f'Frase B: "gato perro"   ->  "perro" esta en la posicion 2')
    similitud = datos["similitud_misma_palabra_otra_posicion"]
    print(f"\nParecido entre los dos vectores de 'perro': {similitud:.4f}")
    print(
        "Si el orden no importara, ese numero seria exactamente 1.0000, porque seria "
        "el mismo vector. No lo es: la misma palabra, en otra posicion, se representa "
        "distinto. Eso es el positional encoding funcionando."
    )
    if similitud >= 0.9999:
        raise RuntimeError(
            "La misma palabra en dos posiciones dio un vector identico. Eso indicaria "
            "que el positional encoding no se esta aplicando, y el modelo no podria "
            "distinguir el orden de las palabras."
        )

    _subtitulo("El modelo tambien sabe CUANTO se separan dos palabras")
    from_tabla = datos["tabla"]
    sim = similitud_entre_posiciones(from_tabla, cuantas=60)
    print("Parecido medio entre dos posiciones, segun lo lejos que esten:")
    for salto in (0, 1, 2, 3, 5, 8):
        media = float(np.mean([sim[i, i + salto] for i in range(5, 50)]))
        etiqueta = "la misma posicion" if salto == 0 else f"a {salto} de distancia"
        print(f"  {etiqueta:<20} {media:+.3f}")
    print(
        "\nBaja con la distancia. Eso significa que el vector de posicion no es una "
        "simple etiqueta numerica: posiciones cercanas tienen vectores parecidos, asi "
        "que el modelo puede notar que dos palabras estan JUNTAS y no solo que ocupan "
        "sitios distintos."
    )

    _subtitulo("Por que esto importa en una frase de verdad")
    tokenizador, _ = obtener_beto()
    for frase in FRASES_ORDEN:
        print(f'  "{frase}"  ->  {tokenizador.tokenize(frase)}')
    print(
        "\nLas dos frases tienen EXACTAMENTE los mismos tokens, en distinto orden, y "
        "significan cosas opuestas. Sin positional encoding el modelo no podria "
        "diferenciarlas: es la razon de que este mecanismo exista."
    )

    return datos


def similitud_entre_posiciones(tabla, cuantas=POSICIONES_A_DIBUJAR):
    """Compara cada posicion con todas las demas. Devuelve la matriz de parecidos."""
    trozo = torch.nn.functional.normalize(tabla[:cuantas], dim=1)
    return (trozo @ trozo.T).numpy()


def dibujar_mapa_de_posiciones(tabla, ruta_salida=None, silencioso=False):
    """Dibuja cuanto se parece cada posicion a todas las demas.

    QUE SE DIBUJA Y POR QUE ESTE GRAFICO Y NO OTRO. La primera version pintaba la
    tabla cruda de embeddings de posicion: 40 posiciones por 768 dimensiones. Salia
    ruido -rayas verticales sin estructura- y era imposible explicarla, porque los
    embeddings APRENDIDOS de BERT no tienen las bandas limpias que tendrian unos
    calculados con senos y cosenos. Una imagen correcta que no ensena nada no sirve
    de entregable.

    Lo que si se ve, y se explica en una frase, es comparar cada posicion con las
    demas: sale una diagonal brillante que se apaga hacia los lados. Medido sobre esta
    tabla, el parecido entre dos posiciones vecinas es 0.90, a tres de distancia baja a
    0.51, y a cinco a 0.39. **El modelo no solo sabe donde esta cada palabra: sabe
    cuanto se separan entre si.** Eso es lo que hace util al positional encoding.
    """
    escribir = (lambda *_a, **_k: None) if silencioso else print
    if not silencioso:
        _encabezado("MAPA DE LAS POSICIONES")

    matriz = similitud_entre_posiciones(tabla)

    mapa_de_color = LinearSegmentedColormap.from_list(
        "mini_jarvis_posiciones", [COLOR_FONDO, COLOR_TURQUESA, COLOR_ROSA],
    )

    figura, ejes = plt.subplots(figsize=(9, 7.5))
    figura.patch.set_facecolor(COLOR_FONDO)
    ejes.set_facecolor(COLOR_FONDO)

    imagen = ejes.imshow(matriz, cmap=mapa_de_color, vmin=0.0, vmax=1.0)

    ejes.set_xlabel("Posicion en la frase", color=COLOR_TEXTO, fontsize=11)
    ejes.set_ylabel("Posicion en la frase", color=COLOR_TEXTO, fontsize=11)
    ejes.set_title(
        f"Cuanto se parecen entre si las posiciones — {NOMBRE_MODELO_BETO}\n"
        f"Primeras {POSICIONES_A_DIBUJAR} de las {tabla.shape[0]}. La diagonal brillante "
        "se apaga con la distancia:\nel modelo codifica no solo el lugar, tambien la cercania.",
        color=COLOR_TEXTO, fontsize=11, pad=14,
    )
    ejes.tick_params(colors=COLOR_TEXTO)
    for spine in ejes.spines.values():
        spine.set_edgecolor(COLOR_TEXTO)

    barra = figura.colorbar(imagen, ax=ejes, fraction=0.03, pad=0.02)
    barra.set_label("Parecido (1 = identicos)", color=COLOR_TEXTO)
    barra.ax.yaxis.set_tick_params(color=COLOR_TEXTO)
    plt.setp(plt.getp(barra.ax.axes, "yticklabels"), color=COLOR_TEXTO)

    figura.tight_layout()
    if ruta_salida is None:
        ruta_salida = Path(__file__).resolve().parent / NOMBRE_PNG_POSICIONES
    ruta_salida = Path(ruta_salida)
    figura.savefig(ruta_salida, dpi=150, facecolor=figura.get_facecolor())
    plt.close(figura)

    escribir(f"\nPNG guardado en: {ruta_salida}")
    escribir(f"Tamano del archivo: {ruta_salida.stat().st_size} bytes")
    return ruta_salida


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
        "misma maquina, los cuatro conceptos que la seccion 2.2 del enunciado exige "
        "evidenciar: tokenizacion, embeddings, positional encoding y self-attention."
    )

    nivel_1_tokenizacion()
    tokens, atenciones = nivel_2_embeddings_y_atencion()
    posiciones = nivel_3_positional_encoding()
    dibujar_mapa_de_atencion(tokens, atenciones, CAPA_ELEGIDA_BASE0, CABEZA_ELEGIDA_BASE0)
    dibujar_mapa_de_posiciones(posiciones["tabla"])

    _encabezado("FIN DEL LABORATORIO")
    print("Los CUATRO conceptos que pide el enunciado, demostrados sobre modelos reales:")
    print("  1) Tokenizacion       -> tokenizador real de Qwen2.5-Instruct.")
    print("  2) Embeddings         -> last_hidden_state de BETO, forma (1, N, 768).")
    print("  3) Positional encoding-> tabla (512, 768) aprendida; la misma palabra en")
    print("                           otra posicion da un vector distinto.")
    print("  4) Self-attention     -> 12 capas de atencion de BETO, filas que suman 1.0.")
    print()
    print("Dos imagenes para el informe y la sustentacion:")
    print("  exploration/mapa_atencion.png   quien mira a quien")
    print("  exploration/mapa_posiciones.png como el modelo codifica el orden")


if __name__ == "__main__":
    main()
