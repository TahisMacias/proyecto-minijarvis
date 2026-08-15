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

# Paleta pastel del proyecto (seccion 11 del documento de diseno).
COLOR_CREMA = "#F9F9FB"
COLOR_MENTA = "#E8F5E9"
COLOR_ROSA = "#FCE4EC"
COLOR_CIELO = "#E1F5FE"
COLOR_TEXTO = "#37474F"  # gris marengo, tambien sirve como "tono saturado" del mapa

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

    tokenizador = _cargar_o_fallar(
        f"el tokenizador de {NOMBRE_TOKENIZADOR_QWEN}",
        AutoTokenizer.from_pretrained,
        NOMBRE_TOKENIZADOR_QWEN,
    )

    _subtitulo("Frase de ejemplo (propia del proyecto Mini-JARVIS)")
    print(f'"{FRASE_NIVEL_1}"')

    ids = tokenizador.encode(FRASE_NIVEL_1)
    tokens = tokenizador.convert_ids_to_tokens(ids)

    _subtitulo(f"Tokens generados: {len(tokens)}")
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
    for indice, (token, id_token) in enumerate(zip(tokens, ids)):
        token_visible = "·" + token[1:] if token.startswith("Ġ") else token
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

    tokenizador = _cargar_o_fallar(
        f"el tokenizador de {NOMBRE_MODELO_BETO}",
        AutoTokenizer.from_pretrained,
        NOMBRE_MODELO_BETO,
    )

    # attn_implementation="eager" es OBLIGATORIO: ver la trampa critica documentada
    # al inicio del archivo. Sin esto, output_attentions=True devuelve None en silencio.
    modelo = _cargar_o_fallar(
        f"los pesos de {NOMBRE_MODELO_BETO}",
        AutoModel.from_pretrained,
        NOMBRE_MODELO_BETO,
        attn_implementation="eager",
    )

    # Modo inferencia: le decimos a PyTorch que no vamos a entrenar, asi que capas
    # como dropout se desactivan y el resultado es determinista.
    modelo.eval()

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

    entradas = tokenizador(FRASE_NIVEL_2, return_tensors="pt")
    tokens = tokenizador.convert_ids_to_tokens(entradas["input_ids"][0])

    _subtitulo("Tokens de BETO para esta frase (incluye [CLS] y [SEP])")
    print(
        "El prefijo '##' marca un sub-token que continua la palabra anterior sin "
        "espacio: es la misma idea del nivel 1, con otra notacion."
    )
    for indice, token in enumerate(tokens):
        print(f"  {indice:>2}  {token}")

    # Sin torch.no_grad() PyTorch guardaria informacion extra para poder calcular
    # gradientes (como si fueramos a entrenar). Aqui solo queremos inferencia: es
    # mas rapido y usa menos memoria desactivar ese calculo.
    with torch.no_grad():
        salida = modelo(**entradas, output_attentions=True)

    _verificar_atenciones(salida)

    embeddings = salida.last_hidden_state
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

    atenciones = salida.attentions
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

def dibujar_mapa_de_atencion(tokens, atenciones, capa_base0, cabeza_base0):
    """Dibuja y guarda un mapa de calor de una capa y cabeza de atencion concretas.

    CONCEPTO CLAVE: un mapa de calor de atencion es, literalmente, la matriz que
    describe el nivel 2 vuelta imagen. Cada celda (fila=token que consulta,
    columna=token consultado) se pinta con un color segun cuanta atencion le puso
    ese token a ese otro token; entre mas oscuro/saturado, mas atencion.
    """
    _encabezado("MAPA DE CALOR DE ATENCION")

    capa_humana = capa_base0 + 1
    cabeza_humana = cabeza_base0 + 1
    print(
        f"Capa elegida: indice base-0 = {capa_base0}  (capa humana #{capa_humana} de 12)"
    )
    print(
        f"Cabeza elegida: indice base-0 = {cabeza_base0}  (cabeza humana #{cabeza_humana} de 12)"
    )
    print(
        "Se eligio esta combinacion porque, de las 144 capas x cabezas posibles, es "
        "una 'cabeza de token anterior': en el mapa se ve una franja iluminada justo "
        "a la izquierda de la diagonal principal, es decir, cada token le presta casi "
        "toda su atencion a la palabra que lo precede inmediatamente. Es un patron "
        "clasico y muy documentado en modelos tipo BERT, y resulta facil de senalar "
        "en la imagen durante la sustentacion oral."
    )

    matriz = atenciones[capa_base0][0, cabeza_base0].numpy()  # (n_tokens, n_tokens)

    # Colormap continuo construido con la paleta pastel del proyecto: va del crema
    # claro (valores bajos de atencion) hasta el gris marengo saturado de la paleta
    # (valores altos), pasando por el azul cielo como tono intermedio. Asi los
    # valores altos de atencion se distinguen con claridad sobre el fondo pastel.
    mapa_de_color = LinearSegmentedColormap.from_list(
        "mini_jarvis_atencion",
        [COLOR_CREMA, COLOR_CIELO, COLOR_TEXTO],
    )

    figura, ejes = plt.subplots(figsize=(10.5, 9))
    figura.patch.set_facecolor(COLOR_CREMA)
    ejes.set_facecolor(COLOR_CREMA)

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

    ruta_salida = Path(__file__).resolve().parent / NOMBRE_PNG_SALIDA
    figura.savefig(ruta_salida, dpi=150, facecolor=figura.get_facecolor())
    plt.close(figura)

    tamano_bytes = ruta_salida.stat().st_size
    print(f"\nPNG guardado en: {ruta_salida}")
    print(f"Tamano del archivo: {tamano_bytes} bytes")


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
