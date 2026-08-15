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
