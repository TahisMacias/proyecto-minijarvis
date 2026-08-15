"""Pruebas de la senal visual de los estados (apoyo del check humano H-09).

El criterio de aceptacion de T-10 dice que **dos estados compartiendo color es un NO
APTO automatico**: incumple H-09 y deja fuera a las personas con daltonismo. Ese
defecto ya ocurrio una vez en este proyecto (RESPONDIENDO y ATENCION compartian rosa
palido; lo detecto el Obrero durante T-03), asi que aqui queda una prueba que lo
impide en silencio para siempre.

No se abre ninguna ventana: se verifica la configuracion y el codigo, no el dibujo.
Asi la suite sigue corriendo en cualquier maquina, con o sin pantalla.
"""

import ast
from pathlib import Path

from config import COLOR_POR_ESTADO, PALETA


ESTADOS_ACTIVOS = ["ESCUCHANDO", "PENSANDO", "RESPONDIENDO", "ATENCION"]


def test_los_cuatro_estados_activos_tienen_color_propio():
    colores = [COLOR_POR_ESTADO[estado] for estado in ESTADOS_ACTIVOS]
    assert len(set(colores)) == 4, (
        "dos estados comparten color: es NO APTO automatico por H-09, porque una "
        f"persona con daltonismo no podria distinguirlos. Colores: {colores}"
    )


def test_todos_los_estados_del_diseno_tienen_color():
    for estado in ESTADOS_ACTIVOS:
        assert estado in COLOR_POR_ESTADO, f"falta el color de {estado}"


def test_los_colores_de_estado_salen_de_la_paleta():
    """Ningun color suelto: la coherencia visual depende de usar los mismos tintes."""
    for estado, color in COLOR_POR_ESTADO.items():
        assert color in PALETA.values(), (
            f"{estado} usa {color}, que no esta en la paleta del proyecto"
        )


def test_cada_estado_tiene_ademas_su_propia_forma():
    """H-09 pide color Y forma: se comprueba que exista una funcion de dibujo distinta.

    Se lee el codigo fuente en vez de abrir una ventana para que la prueba corra en
    cualquier maquina. Si alguien borrara una forma y dejara dos estados dibujandose
    igual, esto lo detiene.
    """
    fuente = Path(__file__).resolve().parents[1] / "gui" / "desktop_app.py"
    arbol = ast.parse(fuente.read_text(encoding="utf-8"))

    dibujantes = {
        nodo.name for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.FunctionDef) and nodo.name.startswith("_dibujar_")
    }

    # Una por estado activo, mas la de reposo, mas el despachador _dibujar_estado.
    esperadas = {
        "_dibujar_estado",
        "_dibujar_circulo_con_pulso",  # ESCUCHANDO
        "_dibujar_puntos",             # PENSANDO
        "_dibujar_onda",               # RESPONDIENDO
        "_dibujar_triangulo",          # ATENCION
        "_dibujar_reposo",             # REPOSO
    }
    faltantes = esperadas - dibujantes
    assert not faltantes, f"faltan formas propias para: {sorted(faltantes)}"


# --- Borde saturado: la senal que si se puede nombrar -----------------------

def test_cada_estado_tiene_borde_saturado_propio():
    """Defecto reportado por la duena: el verde menta se veia azul en pantalla.

    Los tintes de nivel 50 son casi blancos. Como decoracion funcionan; como senal
    no. El borde saturado es lo que hace que el estado se pueda nombrar de un vistazo.
    """
    from config import COLOR_BORDE_POR_ESTADO

    bordes = [COLOR_BORDE_POR_ESTADO[estado] for estado in ESTADOS_ACTIVOS]
    assert len(set(bordes)) == 4, f"dos estados comparten borde: {bordes}"


def test_el_borde_es_mas_oscuro_que_el_relleno():
    """Si el borde no contrasta con su relleno, no se distingue la figura."""
    from config import COLOR_BORDE_POR_ESTADO, COLOR_POR_ESTADO

    def luminosidad(hexadecimal):
        r, g, b = (int(hexadecimal[i:i + 2], 16) for i in (1, 3, 5))
        # Coeficientes estandar de luminosidad percibida: el ojo humano es mucho mas
        # sensible al verde que al azul.
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    for estado in ESTADOS_ACTIVOS:
        claro = luminosidad(COLOR_POR_ESTADO[estado])
        oscuro = luminosidad(COLOR_BORDE_POR_ESTADO[estado])
        assert claro - oscuro > 80, (
            f"{estado}: el borde {COLOR_BORDE_POR_ESTADO[estado]} no contrasta lo "
            f"suficiente con el relleno {COLOR_POR_ESTADO[estado]}"
        )
