"""Interfaz de escritorio de Mini-JARVIS (tareas T-10, T-13, T-14 y T-19).

Ventana en CustomTkinter, tema oscuro, con la paleta turquesa y rosa de `config.py`.

LA REGLA QUE ORGANIZA ESTE ARCHIVO: el hilo trabajador del orquestador nunca toca un
widget. El orquestador solo sabe llamar a una funcion `notificar(evento)`, y lo que
esta clase le entrega es esto:

    notificar=lambda evento: self.after(0, self._aplicar_evento, evento)

`after(0, ...)` no ejecuta nada en el acto: deja el trabajo en la cola del hilo
principal de Tkinter, que lo atiende en su proximo respiro. Es el unico puente seguro
entre un hilo cualquiera y la interfaz. Todo lo que pinta la ventana vive de este lado.

POR QUE COLOR **Y** FORMA (H-09): los cuatro estados se distinguen sin leer una sola
palabra, y no solo por color. Una persona con daltonismo debe poder operar la
aplicacion: si la unica pista fuera el color, para ella la interfaz no comunicaria
nada. Por eso cada estado tiene ademas su propia figura: circulo lleno, tres puntos,
onda y triangulo. La forma no es decoracion.

REDISENO T-19 (2026-08-17), pedido por la duena
===============================================

Tres cambios de fondo respecto a la ventana anterior:

1. **Tema oscuro con la paleta del personaje** (turquesa y rosa). **No se usa ningun
   arte de terceros**: el repositorio es publico y ese diseno es propiedad de Crypton
   Future Media. Lo que se dibuja aqui es original y sale de codigo -degradado, malla
   y destellos-, usando solo los dos colores, que no son propiedad de nadie.
2. **Se quitan las pestanas.** La conversacion y el laboratorio se ven a la vez, en dos
   columnas. Antes habia que acordarse de cambiar de pestana para ver el analisis; en
   una demostracion en vivo, lo que no esta a la vista no existe.
3. **El mapa de atencion se abre en superposicion** sobre la ventana, grande y con un
   boton de cerrar visible, en vez de vivir encogido dentro de un panel.

Los controles de sustentacion (T-14) se construyen **dentro** de esta distribucion, no
encima de la anterior: sliders de temperatura y top_p, indicador de turnos y tokens que
avisa antes de descartar, visor del system prompt y selector de modelo en caliente.
"""

from __future__ import annotations

import math
import tempfile
import threading
import tkinter
from pathlib import Path

import customtkinter
from PIL import Image

from config import (
    COLOR_BORDE_POR_ESTADO,
    COLOR_POR_ESTADO,
    MAX_TURNOS_MEMORIA,
    MODELO_LLM_ALTERNO,
    MODELO_LLM_PREDETERMINADO,
    PALETA,
    TEMPERATURA_PREDETERMINADA,
    TOP_P_PREDETERMINADO,
)
from core.orchestrator import Estado, TipoEvento


# --- Constantes de presentacion --------------------------------------------

TITULO = "Mini-JARVIS"

ANCHO_VENTANA = 1040          # dos columnas: conversacion y laboratorio
ALTO_VENTANA = 720
FRACCION_MAXIMA_DE_PANTALLA = 0.88

MILIS_ANTIRREBOTE_ESPACIO = 60

LADO_LIENZO = 210             # el modulo de estado, mas grande que antes (T-19)
MILIS_ANIMACION = 90

LEYENDA_POR_ESTADO = {
    Estado.REPOSO: "Listo. Manten presionado para hablar.",
    Estado.ESCUCHANDO: "Te escucho...",
    Estado.PENSANDO: "Pensando...",
    Estado.RESPONDIENDO: "Respondiendo...",
    Estado.ATENCION: "Atencion",
}

# REPOSO no esta en la tabla de estados del diseno porque no es un estado de actividad.
# Se le da el turquesa apagado del propio fondo: presente pero dormido, sin competir
# con los cuatro colores que si significan algo.
RELLENO_REPOSO = PALETA["superficie_alta"]
BORDE_REPOSO = PALETA["texto_tenue"]


class AplicacionMiniJarvis(customtkinter.CTk):
    """Ventana principal. Solo pinta y recoge pulsaciones; no piensa por su cuenta."""

    def __init__(self, crear_orquestador, motor=None, memoria=None) -> None:
        super().__init__()

        customtkinter.set_appearance_mode("dark")
        self.title(TITULO)
        self.geometry(f"{self._ancho_que_cabe()}x{self._alto_que_cabe()}")
        self.minsize(880, 560)
        self.configure(fg_color=PALETA["fondo_profundo"])

        # `motor` y `memoria` llegan para los controles de sustentacion (T-14): los
        # sliders necesitan un motor al que aplicarles el muestreo y el indicador
        # necesita una memoria que contar. Son opcionales para que la ventana se pueda
        # abrir sin ellos en una prueba.
        self._motor = motor
        self._memoria = memoria

        self._estado = Estado.REPOSO
        self._paso_animacion = 0
        self._espacio_presionado = False
        self._analisis_en_curso = False
        self._imagen_mapa = None
        self._imagen_superpuesta = None
        self._ruta_mapa_actual = None
        self._superposicion = None
        self._cierre_de_espacio_pendiente = None

        self._temperatura = TEMPERATURA_PREDETERMINADA
        self._top_p = TOP_P_PREDETERMINADO

        self._construir()

        self._orquestador = crear_orquestador(self._notificar_desde_otro_hilo)

        self._animar()
        self._refrescar_indicador_de_memoria()
        self.after(120, self._tomar_el_foco)

    # --- Tamano de ventana ---------------------------------------------------

    def _escala(self) -> float:
        return customtkinter.ScalingTracker.get_window_scaling(self)

    def _alto_que_cabe(self) -> int:
        """Altura que de verdad entra en esta pantalla.

        Windows suele venir con escalado al 125 % o al 150 %: una ventana declarada de
        720 se dibuja de 900 pixeles reales, y el boton de hablar termina debajo de la
        barra de tareas. Se comprobo en esta maquina, con escalado 133 %.
        """
        disponible = (self.winfo_screenheight() * FRACCION_MAXIMA_DE_PANTALLA) / self._escala()
        return int(min(ALTO_VENTANA, disponible))

    def _ancho_que_cabe(self) -> int:
        """Lo mismo para el ancho: la ventana nueva es de dos columnas y es ancha."""
        disponible = (self.winfo_screenwidth() * FRACCION_MAXIMA_DE_PANTALLA) / self._escala()
        return int(min(ANCHO_VENTANA, disponible))

    # --- Construccion de la ventana ------------------------------------------

    def _construir(self) -> None:
        # Los minsize NO son decorativos. Sin ellos, un texto largo dentro de una
        # columna la ensancha y aplasta a las vecinas: al llenarse la memoria, el aviso
        # de descarte hacia crecer la columna central y la del laboratorio se quedaba
        # con el titulo y el boton cortados. Se vio abriendo la ventana con la memoria
        # llena, no leyendo el codigo.
        self.grid_columnconfigure(0, weight=0, minsize=300)  # izquierda: estado
        self.grid_columnconfigure(1, weight=3, minsize=380)  # centro: conversacion
        self.grid_columnconfigure(2, weight=2, minsize=330)  # derecha: laboratorio
        self.grid_rowconfigure(0, weight=1)

        self._construir_columna_estado()
        self._construir_columna_conversacion()
        self._construir_columna_laboratorio()

        self.bind_all("<KeyPress-space>", self._al_presionar_espacio)
        self.bind_all("<KeyRelease-space>", self._al_soltar_espacio)
        self.bind_all("<Escape>", lambda _e: self._cerrar_superposicion())
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        self._escribir(
            "Mini-JARVIS",
            "Hola. Soy una inteligencia artificial, asi que mis respuestas pueden "
            "contener errores. Manten presionado el boton y hablame.",
        )

    # --- Columna izquierda: el modulo de estado, ahora grande (T-19) ---------

    def _construir_columna_estado(self) -> None:
        marco = customtkinter.CTkFrame(self, fg_color=PALETA["superficie"], corner_radius=18)
        marco.grid(row=0, column=0, sticky="nsew", padx=(14, 7), pady=14)
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(2, weight=1)

        customtkinter.CTkLabel(
            marco, text=TITULO, text_color=PALETA["turquesa"],
            font=("Segoe UI", 30, "bold"),
        ).grid(row=0, column=0, pady=(22, 2))

        customtkinter.CTkLabel(
            marco, text="asistente de voz", text_color=PALETA["rosa"],
            font=("Segoe UI", 12),
        ).grid(row=1, column=0, pady=(0, 10))

        self._lienzo = tkinter.Canvas(
            marco, width=LADO_LIENZO, height=LADO_LIENZO,
            highlightthickness=0, bg=PALETA["superficie"],
        )
        self._lienzo.grid(row=2, column=0, pady=4)

        self._leyenda = customtkinter.CTkLabel(
            marco, text=LEYENDA_POR_ESTADO[Estado.REPOSO],
            text_color=PALETA["texto_claro"], font=("Segoe UI", 15), wraplength=250,
        )
        self._leyenda.grid(row=3, column=0, pady=(6, 12))

        self._boton = customtkinter.CTkButton(
            marco, text="Manten presionado para hablar", height=58, corner_radius=29,
            fg_color=PALETA["superficie_alta"], hover_color=PALETA["turquesa"],
            text_color=PALETA["texto_claro"], font=("Segoe UI", 14, "bold"),
            border_width=3, border_color=BORDE_REPOSO,
        )
        self._boton.grid(row=4, column=0, padx=18, pady=(0, 6), sticky="ew")
        self._boton.bind("<ButtonPress-1>", self._al_presionar)
        self._boton.bind("<ButtonRelease-1>", self._al_soltar)

        customtkinter.CTkLabel(
            marco, text="la barra espaciadora hace lo mismo",
            text_color=PALETA["texto_tenue"], font=("Segoe UI", 10),
        ).grid(row=5, column=0, pady=(0, 16))

    # --- Columna central: conversacion + controles de sustentacion (T-14) ----

    def _construir_columna_conversacion(self) -> None:
        marco = customtkinter.CTkFrame(self, fg_color=PALETA["superficie"], corner_radius=18)
        marco.grid(row=0, column=1, sticky="nsew", padx=7, pady=14)
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(1, weight=1)

        self._encabezado(marco, "Conversacion").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self._conversacion = customtkinter.CTkTextbox(
            marco, fg_color=PALETA["fondo_profundo"], text_color=PALETA["texto_claro"],
            border_width=0, font=("Segoe UI", 13), wrap="word", corner_radius=12,
        )
        self._conversacion.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
        self._conversacion.configure(state="disabled")

        self._construir_controles(marco).grid(
            row=2, column=0, sticky="ew", padx=14, pady=(0, 14))

    def _construir_controles(self, contenedor):
        """Controles de sustentacion (T-14), dentro de la distribucion nueva.

        No estan escondidos en un menu a proposito: la sustentacion consiste en
        ensenar el efecto de estos numeros en vivo, asi que tienen que estar a la vista
        y al lado de la conversacion sobre la que actuan.
        """
        marco = customtkinter.CTkFrame(contenedor, fg_color=PALETA["superficie_alta"],
                                       corner_radius=12)
        marco.grid_columnconfigure(1, weight=1)

        # --- Selector de modelo, en caliente ---
        customtkinter.CTkLabel(
            marco, text="Modelo", text_color=PALETA["texto_tenue"],
            font=("Segoe UI", 11),
        ).grid(row=0, column=0, sticky="w", padx=(12, 8), pady=(10, 4))

        self._selector_modelo = customtkinter.CTkOptionMenu(
            marco,
            values=[MODELO_LLM_PREDETERMINADO, MODELO_LLM_ALTERNO],
            command=self._cambiar_modelo,
            fg_color=PALETA["superficie"], button_color=PALETA["turquesa"],
            button_hover_color=PALETA["rosa"], text_color=PALETA["texto_claro"],
            font=("Segoe UI", 11), dropdown_font=("Segoe UI", 11),
        )
        self._selector_modelo.grid(row=0, column=1, columnspan=2, sticky="ew",
                                   padx=(0, 12), pady=(10, 4))

        # --- Sliders de muestreo ---
        self._slider_temperatura, self._valor_temperatura = self._construir_slider(
            marco, fila=1, etiqueta="Temperatura", minimo=0.0, maximo=1.5,
            inicial=TEMPERATURA_PREDETERMINADA, al_mover=self._cambiar_temperatura)

        self._slider_top_p, self._valor_top_p = self._construir_slider(
            marco, fila=2, etiqueta="top_p", minimo=0.1, maximo=1.0,
            inicial=TOP_P_PREDETERMINADO, al_mover=self._cambiar_top_p)

        # --- Indicador de memoria ---
        # wraplength para que el aviso de descarte, que es la frase mas larga de la
        # ventana, se parta en dos lineas en vez de ensanchar la columna.
        self._indicador_memoria = customtkinter.CTkLabel(
            marco, text="", text_color=PALETA["texto_tenue"], font=("Segoe UI", 11),
            anchor="w", justify="left", wraplength=300,
        )
        self._indicador_memoria.grid(row=3, column=0, columnspan=2, sticky="w",
                                     padx=12, pady=(6, 10))

        customtkinter.CTkButton(
            marco, text="Ver system prompt", width=130, height=26,
            fg_color=PALETA["superficie"], hover_color=PALETA["turquesa"],
            text_color=PALETA["texto_claro"], font=("Segoe UI", 11),
            command=self._mostrar_system_prompt,
        ).grid(row=3, column=2, sticky="e", padx=(0, 12), pady=(6, 10))

        return marco

    def _construir_slider(self, contenedor, fila, etiqueta, minimo, maximo,
                          inicial, al_mover):
        customtkinter.CTkLabel(
            contenedor, text=etiqueta, text_color=PALETA["texto_tenue"],
            font=("Segoe UI", 11),
        ).grid(row=fila, column=0, sticky="w", padx=(12, 8), pady=2)

        slider = customtkinter.CTkSlider(
            contenedor, from_=minimo, to=maximo, command=al_mover,
            fg_color=PALETA["superficie"], progress_color=PALETA["turquesa"],
            button_color=PALETA["rosa"], button_hover_color=PALETA["texto_claro"],
            height=16,
        )
        slider.set(inicial)
        slider.grid(row=fila, column=1, sticky="ew", padx=(0, 8), pady=2)

        valor = customtkinter.CTkLabel(
            contenedor, text=f"{inicial:.2f}", text_color=PALETA["turquesa"],
            font=("Consolas", 12), width=44,
        )
        valor.grid(row=fila, column=2, sticky="e", padx=(0, 12), pady=2)
        return slider, valor

    # --- Columna derecha: el laboratorio, ya sin pestana (T-13 + T-19) -------

    def _construir_columna_laboratorio(self) -> None:
        """El laboratorio, ahora visible a la vez que la conversacion.

        Muestra, sobre la ULTIMA frase que dijo la usuaria: como se corta en tokens y
        que numero le toca a cada uno, y el mapa de atencion de BETO para esa misma
        frase. Es la respuesta visual a la pregunta de sustentacion sobre tokenizacion
        y self-attention: no con un ejemplo de libro, sino con lo que se acaba de decir.

        Todo el calculo lo hace `exploration/transformer_lab.py`. Aqui no se
        reimplementa nada: si el laboratorio y esta columna dijeran cosas distintas,
        una de las dos estaria mintiendo en la sustentacion.
        """
        marco = customtkinter.CTkFrame(self, fg_color=PALETA["superficie"], corner_radius=18)
        marco.grid(row=0, column=2, sticky="nsew", padx=(7, 14), pady=14)
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(2, weight=1)

        self._encabezado(marco, "Laboratorio del Transformer").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        # anchor y justify a la izquierda, y wraplength holgado respecto al ancho de
        # la columna: con el escalado de Windows al 133 % un wraplength de 280 se
        # dibuja mas ancho que la columna y la frase se salia por los dos lados.
        # Se comprobo abriendo la ventana, no leyendo el codigo.
        self._laboratorio_frase = customtkinter.CTkLabel(
            marco, text="Habla y aqui aparecera el analisis de lo que dijiste.",
            text_color=PALETA["texto_tenue"], font=("Segoe UI", 11, "italic"),
            wraplength=195, justify="left", anchor="w",
        )
        self._laboratorio_frase.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        self._laboratorio_tokens = customtkinter.CTkTextbox(
            marco, fg_color=PALETA["fondo_profundo"], text_color=PALETA["texto_claro"],
            border_width=0, font=("Consolas", 11), wrap="none", corner_radius=12,
        )
        self._laboratorio_tokens.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 8))
        self._laboratorio_tokens.configure(state="disabled")

        self._boton_mapa = customtkinter.CTkButton(
            marco, text="Ver el mapa de atencion", height=40, corner_radius=20,
            fg_color=PALETA["superficie_alta"], hover_color=PALETA["rosa"],
            text_color=PALETA["texto_claro"], font=("Segoe UI", 12, "bold"),
            border_width=2, border_color=PALETA["rosa"],
            command=self._abrir_superposicion_del_mapa, state="disabled",
        )
        self._boton_mapa.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 16))

    def _encabezado(self, contenedor, texto):
        return customtkinter.CTkLabel(
            contenedor, text=texto.upper(), text_color=PALETA["turquesa"],
            font=("Segoe UI", 12, "bold"),
        )

    # --- Controles de sustentacion: que hacen (T-14) -------------------------

    def _cambiar_temperatura(self, valor: float) -> None:
        self._temperatura = float(valor)
        self._valor_temperatura.configure(text=f"{self._temperatura:.2f}")
        self._aplicar_muestreo()

    def _cambiar_top_p(self, valor: float) -> None:
        self._top_p = float(valor)
        self._valor_top_p.configure(text=f"{self._top_p:.2f}")
        self._aplicar_muestreo()

    def _aplicar_muestreo(self) -> None:
        """Deja el muestreo listo para la SIGUIENTE respuesta, no para la actual.

        Se guarda en el motor en vez de pasarlo por el orquestador para no cambiarle la
        firma a un modulo que ya estaba cerrado y auditado. El motor lo aplica en su
        proxima llamada.
        """
        if self._motor is not None:
            self._motor.temperatura = self._temperatura
            self._motor.top_p = self._top_p

    def _cambiar_modelo(self, modelo: str) -> None:
        """Cambia de modelo sin reiniciar y sin perder la conversacion."""
        if self._motor is None:
            return
        try:
            self._motor.cambiar_modelo(modelo)
        except Exception:  # noqa: BLE001 - un selector nunca tumba la ventana
            self._escribir("Aviso", "No se pudo cambiar de modelo.")
            return
        corto = modelo.split("/")[-1]
        self._escribir("Aviso", f"A partir de ahora responde {corto}. La conversacion sigue.")

    def _refrescar_indicador_de_memoria(self) -> None:
        """Turnos y tokens en memoria, avisando ANTES de que se descarte el mas viejo.

        El aviso es el punto interesante para la sustentacion: deja senalar el momento
        exacto en que la ventana de contexto empieza a olvidar.
        """
        if self._memoria is not None:
            turnos = self._memoria.numero_de_turnos()
            tokens = self._memoria.estimar_tokens()
            if self._memoria.esta_llena():
                texto = (f"Memoria {turnos}/{MAX_TURNOS_MEMORIA} - {tokens} tokens\n"
                         "El proximo turno ya descarta el mas antiguo.")
                color = PALETA["rosa"]
            else:
                texto = f"Memoria {turnos}/{MAX_TURNOS_MEMORIA} turnos - {tokens} tokens aprox."
                color = PALETA["texto_tenue"]
            self._indicador_memoria.configure(text=texto, text_color=color)
        self.after(700, self._refrescar_indicador_de_memoria)

    def _mostrar_system_prompt(self) -> None:
        """Visor de solo lectura: lo que se le dice al modelo antes de cada turno."""
        from core.llm_engine import SYSTEM_PROMPT
        self._abrir_superposicion(
            "System prompt (solo lectura)",
            constructor=lambda padre: self._caja_de_texto(padre, SYSTEM_PROMPT),
        )

    def _caja_de_texto(self, padre, contenido: str):
        caja = customtkinter.CTkTextbox(
            padre, fg_color=PALETA["fondo_profundo"], text_color=PALETA["texto_claro"],
            font=("Segoe UI", 13), wrap="word", border_width=0, corner_radius=12,
        )
        caja.insert("1.0", contenido)
        caja.configure(state="disabled")
        return caja

    # --- Superposicion: el mapa grande y el system prompt (T-19) -------------

    def _abrir_superposicion_del_mapa(self) -> None:
        if self._ruta_mapa_actual is None:
            return
        self._abrir_superposicion(
            "Mapa de atencion de tu ultima frase",
            constructor=self._lienzo_del_mapa,
        )

    def _lienzo_del_mapa(self, padre):
        """Carga el PNG del mapa y lo encaja en la ventana.

        NO SE CIERRA LA IMAGEN AQUI, y la primera version de este metodo si lo hacia:
        se abria con `Image.open`, se construia el CTkImage y se cerraba en un
        `finally`. Reventaba con "Operation on closed image" al abrir la
        superposicion. El motivo es que Pillow carga los pixeles de forma PEREZOSA:
        `Image.open` solo lee la cabecera, y CustomTkinter no pide los datos hasta que
        va a dibujar de verdad, que ocurre despues del `finally`.

        La solucion es guardar la imagen viva en el objeto y cerrar la ANTERIOR al
        abrir una nueva. Asi no se acumulan descriptores abiertos turno tras turno y
        tampoco se cierra ninguna antes de tiempo.
        """
        anterior = getattr(self, "_pil_mapa", None)
        if anterior is not None:
            try:
                anterior.close()
            except Exception:  # noqa: BLE001 - cerrar una imagen vieja nunca es critico
                pass

        imagen = Image.open(self._ruta_mapa_actual)
        self._pil_mapa = imagen

        # Se encaja conservando la proporcion. Se mide la VENTANA y no la pantalla:
        # la superposicion vive dentro de la ventana, no fuera.
        ancho_max = max(self.winfo_width() - 160, 480)
        alto_max = max(self.winfo_height() - 220, 360)
        proporcion = imagen.height / imagen.width
        ancho = min(ancho_max, int(alto_max / proporcion))

        self._imagen_superpuesta = customtkinter.CTkImage(
            light_image=imagen, dark_image=imagen,
            size=(ancho, int(ancho * proporcion)),
        )
        return customtkinter.CTkLabel(padre, text="", image=self._imagen_superpuesta)

    def _abrir_superposicion(self, titulo: str, constructor) -> None:
        """Cubre la ventana con un panel y un boton de cerrar bien visible.

        Se usa un `place` sobre la ventana en vez de una ventana aparte a proposito: una
        segunda ventana se puede perder detras de la principal durante una demostracion,
        y en un proyector eso parece que la aplicacion se colgo. Se cierra con el boton,
        con la tecla Escape o pulsando fuera del panel.
        """
        self._cerrar_superposicion()

        velo = customtkinter.CTkFrame(self, fg_color=PALETA["fondo_profundo"],
                                      corner_radius=0)
        velo.place(relx=0, rely=0, relwidth=1, relheight=1)
        velo.bind("<Button-1>", lambda _e: self._cerrar_superposicion())

        panel = customtkinter.CTkFrame(velo, fg_color=PALETA["superficie"],
                                       corner_radius=18, border_width=2,
                                       border_color=PALETA["turquesa"])
        panel.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.9)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        barra = customtkinter.CTkFrame(panel, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        barra.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(
            barra, text=titulo, text_color=PALETA["turquesa"],
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, sticky="w")

        # El boton de cerrar es grande y esta siempre a la vista: es un criterio
        # explicito de T-19. Una superposicion de la que no se sabe salir da mas miedo
        # en vivo que no tenerla.
        customtkinter.CTkButton(
            barra, text="Cerrar  ✕", width=110, height=34, corner_radius=17,
            fg_color=PALETA["rosa"], hover_color=PALETA["turquesa"],
            text_color=PALETA["fondo_profundo"], font=("Segoe UI", 13, "bold"),
            command=self._cerrar_superposicion,
        ).grid(row=0, column=1, sticky="e")

        contenido = constructor(panel)
        contenido.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        self._superposicion = velo

    def _cerrar_superposicion(self) -> None:
        if self._superposicion is not None:
            self._superposicion.destroy()
            self._superposicion = None

    # --- Entrada de la usuaria -----------------------------------------------

    def _al_presionar(self, evento=None) -> None:
        self._orquestador.empezar_a_escuchar()

    def _al_soltar(self, evento=None) -> None:
        self._orquestador.terminar_y_responder()

    def _al_presionar_espacio(self, evento=None) -> None:
        """Inicio de la escucha por teclado, a prueba de la repeticion automatica.

        EL PROBLEMA QUE RESUELVE ESTO: mientras una tecla sigue hundida, el sistema la
        repite. Segun la maquina, esa repeticion puede llegar como una ristra de
        KeyPress sueltos o como PAREJAS de soltar+presionar decenas de veces por
        segundo. En el segundo caso, mantener la barra espaciadora cerraba el microfono
        a los milisegundos de abrirlo: la usuaria hablaba y no se grababa nada. Ignorar
        solo el KeyPress repetido no bastaba, porque el que hacia dano era el
        KeyRelease falso.

        La solucion es no creerle a un KeyRelease de inmediato: se espera un instante y,
        si llega otro KeyPress en ese margen, era repeticion y se cancela el cierre. Un
        dedo humano no suelta y vuelve a presionar en 60 milisegundos; la repeticion
        automatica, si.
        """
        if self._cierre_de_espacio_pendiente is not None:
            self.after_cancel(self._cierre_de_espacio_pendiente)
            self._cierre_de_espacio_pendiente = None
            return
        if self._espacio_presionado:
            return
        self._espacio_presionado = True
        self._al_presionar()

    def _al_soltar_espacio(self, evento=None) -> None:
        if not self._espacio_presionado or self._cierre_de_espacio_pendiente is not None:
            return
        self._cierre_de_espacio_pendiente = self.after(
            MILIS_ANTIRREBOTE_ESPACIO, self._cerrar_escucha_por_teclado
        )

    def _cerrar_escucha_por_teclado(self) -> None:
        """Se solto de verdad: pasaron los milisegundos sin ninguna repeticion."""
        self._cierre_de_espacio_pendiente = None
        self._espacio_presionado = False
        self._al_soltar()

    def _al_cerrar(self) -> None:
        """Cierra sin dejar el microfono tomado ni un turno a medias."""
        try:
            self._orquestador.cancelar_escucha()
        except Exception:  # noqa: BLE001 - cerrar nunca debe fallar hacia la usuaria
            pass
        self.destroy()

    # --- Puente entre hilos ---------------------------------------------------

    def _notificar_desde_otro_hilo(self, evento) -> None:
        """Lo unico que el orquestador puede llamar. NO toca widgets: solo encola."""
        self.after(0, self._aplicar_evento, evento)

    def _aplicar_evento(self, evento) -> None:
        """Ya corre en el hilo principal: aqui si se pueden tocar los widgets."""
        if evento.tipo is TipoEvento.ESTADO:
            self._cambiar_estado(evento.estado)
        elif evento.tipo is TipoEvento.TRANSCRIPCION:
            self._escribir("Tu", evento.texto)
            self._analizar_en_segundo_plano(evento.texto)
        elif evento.tipo is TipoEvento.RESPUESTA:
            self._escribir("Mini-JARVIS", evento.texto)
        elif evento.tipo is TipoEvento.HERRAMIENTA:
            self._escribir("...", f"usando la herramienta {evento.texto}")
        elif evento.tipo is TipoEvento.ERROR:
            # El texto ya viene redactado para una persona: el orquestador se encarga
            # de que ninguna traza tecnica llegue hasta aqui.
            self._escribir("Aviso", evento.texto)

    # --- Laboratorio (T-13) ---------------------------------------------------

    def _analizar_en_segundo_plano(self, frase: str) -> None:
        """Lanza el analisis del Transformer en un hilo aparte.

        POR QUE UN HILO: la primera vez hay que cargar BETO, que son cientos de
        megabytes y varios segundos. Hacerlo en el hilo de la interfaz dejaria la
        ventana congelada justo despues de hablar, que es el momento en que la usuaria
        esta mirando.

        Si ya hay un analisis corriendo, este se descarta: la frase nueva llegara con
        el siguiente turno y no vale la pena encolar trabajo que ya quedo viejo.
        """
        if self._analisis_en_curso:
            return
        self._analisis_en_curso = True
        self._laboratorio_frase.configure(
            text=f'Analizando: "{frase}"  (la primera vez tarda unos segundos)'
        )
        threading.Thread(
            target=self._analizar, args=(frase,),
            name="minijarvis-laboratorio", daemon=True,
        ).start()

    def _analizar(self, frase: str) -> None:
        """Corre en el hilo del laboratorio. No toca ningun widget: solo calcula."""
        try:
            # Import perezoso a proposito: `transformer_lab` arrastra torch y
            # transformers, que tardan segundos en cargar y ocupan memoria. Si se
            # importara arriba, la aplicacion tardaria eso en abrir aunque nadie
            # llegue a mirar esta columna.
            from exploration import transformer_lab

            filas = transformer_lab.tokenizar_con_qwen(frase)
            analisis = transformer_lab.analizar_con_beto(frase)
            ruta_png = Path(tempfile.gettempdir()) / "minijarvis-atencion.png"
            transformer_lab.dibujar_mapa_de_atencion(
                analisis["tokens"], analisis["atenciones"],
                transformer_lab.CAPA_ELEGIDA_BASE0,
                transformer_lab.CABEZA_ELEGIDA_BASE0,
                ruta_salida=ruta_png, silencioso=True,
            )
            resultado = {
                "frase": frase, "filas": filas,
                "forma": analisis["forma_embeddings"],
                "n_capas": analisis["n_capas"], "n_cabezas": analisis["n_cabezas"],
                "png": ruta_png,
            }
        except Exception as excepcion:  # noqa: BLE001
            # El laboratorio es valor agregado: si falla, la conversacion sigue
            # funcionando igual. No se le arruina el turno a nadie por un grafico.
            resultado = {"frase": frase, "error": str(excepcion)}

        self.after(0, self._pintar_laboratorio, resultado)

    def _pintar_laboratorio(self, resultado: dict) -> None:
        """Ya en el hilo principal: aqui si se pueden tocar los widgets."""
        self._analisis_en_curso = False

        if "error" in resultado:
            self._laboratorio_frase.configure(
                text="No se pudo analizar esta frase. La conversacion no se ve "
                     "afectada; vuelve a intentarlo en el siguiente turno."
            )
            return

        frase = resultado["frase"]
        if len(frase) > 90:
            frase = frase[:90].rstrip() + "..."
        self._laboratorio_frase.configure(text=f'Frase analizada: "{frase}"')

        forma = resultado["forma"]
        lineas = [
            f"TOKENIZACION  ->  {len(resultado['filas'])} tokens",
            "(tokenizador real de Qwen)",
            "",
            f"{'idx':>4}  {'ID':>9}  token",
            f"{'-' * 4}  {'-' * 9}  {'-' * 20}",
        ]
        lineas += [
            f"{indice:>4}  {id_token:>9}  {token}"
            for indice, id_token, token in resultado["filas"]
        ]
        lineas += [
            "",
            f"EMBEDDINGS de BETO: {forma}",
            f"  = 1 frase, {forma[1]} tokens,",
            f"    {forma[2]} numeros por token",
            "",
            f"ATENCION: {resultado['n_capas']} capas",
            f"          x {resultado['n_cabezas']} cabezas",
        ]

        self._laboratorio_tokens.configure(state="normal")
        self._laboratorio_tokens.delete("1.0", "end")
        self._laboratorio_tokens.insert("1.0", "\n".join(lineas))
        self._laboratorio_tokens.configure(state="disabled")

        self._ruta_mapa_actual = resultado["png"]
        self._boton_mapa.configure(state="normal")

    # --- Pintado ---------------------------------------------------------------

    def _cambiar_estado(self, estado: Estado) -> None:
        self._estado = estado
        self._paso_animacion = 0
        self._leyenda.configure(text=LEYENDA_POR_ESTADO.get(estado, ""))
        # El boton acompana al indicador: mismo relleno y mismo borde luminoso.
        self._boton.configure(
            fg_color=COLOR_POR_ESTADO.get(estado.value, RELLENO_REPOSO),
            border_color=COLOR_BORDE_POR_ESTADO.get(estado.value, BORDE_REPOSO),
        )

    def _escribir(self, quien: str, texto: str) -> None:
        self._conversacion.configure(state="normal")
        self._conversacion.insert("end", f"{quien}: {texto}\n\n")
        self._conversacion.see("end")
        self._conversacion.configure(state="disabled")

    # --- Animacion del indicador ------------------------------------------------

    def _animar(self) -> None:
        """Redibuja la figura del estado actual y se vuelve a agendar.

        Se usa `after` en vez de un hilo: la animacion es trabajo de la interfaz y debe
        correr en su hilo, igual que todo lo demas que toca widgets.
        """
        self._paso_animacion += 1
        self._dibujar_estado()
        self.after(MILIS_ANIMACION, self._animar)

    def _dibujar_estado(self) -> None:
        lienzo = self._lienzo
        lienzo.delete("all")

        color = COLOR_POR_ESTADO.get(self._estado.value, RELLENO_REPOSO)
        borde = COLOR_BORDE_POR_ESTADO.get(self._estado.value, BORDE_REPOSO)
        centro = LADO_LIENZO / 2

        self._dibujar_halo(lienzo, centro, borde)

        if self._estado is Estado.ESCUCHANDO:
            self._dibujar_circulo_con_pulso(lienzo, centro, color, borde)
        elif self._estado is Estado.PENSANDO:
            self._dibujar_puntos(lienzo, centro, color, borde)
        elif self._estado is Estado.RESPONDIENDO:
            self._dibujar_onda(lienzo, centro, color, borde)
        elif self._estado is Estado.ATENCION:
            self._dibujar_triangulo(lienzo, centro, color, borde)
        else:
            self._dibujar_reposo(lienzo, centro, borde)

    def _dibujar_halo(self, lienzo, centro, borde) -> None:
        """Arte original: anillos concentricos tenues que giran despacio.

        Es lo unico "decorativo" de la ventana y esta hecho con codigo, no con una
        imagen: el repositorio es publico y no se sube arte de terceros. Da la
        sensacion de aparato encendido sin competir con la figura del estado, que es
        la que comunica.
        """
        fase = self._paso_animacion / 30.0
        for indice in range(3):
            radio = 78 + indice * 9 + math.sin(fase + indice) * 3
            lienzo.create_oval(
                centro - radio, centro - radio, centro + radio, centro + radio,
                outline=borde, width=1, dash=(2, 14),
            )

    def _dibujar_circulo_con_pulso(self, lienzo, centro, color, borde) -> None:
        """ESCUCHANDO: circulo lleno que late despacio, como un microfono abierto."""
        fase = self._paso_animacion % 20
        radio = 52 + (fase if fase <= 10 else 20 - fase) * 1.6
        lienzo.create_oval(
            centro - radio, centro - radio, centro + radio, centro + radio,
            fill=color, outline=borde, width=6,
        )

    def _dibujar_puntos(self, lienzo, centro, color, borde) -> None:
        """PENSANDO: tres puntos que se encienden en secuencia, como quien delibera."""
        encendido = (self._paso_animacion // 4) % 3
        for indice in range(3):
            x = centro + (indice - 1) * 46
            radio = 23 if indice == encendido else 15
            lienzo.create_oval(
                x - radio, centro - radio, x + radio, centro + radio,
                fill=color if indice == encendido else PALETA["superficie"],
                outline=borde, width=5,
            )

    def _dibujar_onda(self, lienzo, centro, color, borde) -> None:
        """RESPONDIENDO: barras de distinta altura, la forma clasica de suena audio."""
        alturas = [30, 54, 76, 54, 30]
        desfase = self._paso_animacion // 2
        for indice, altura_base in enumerate(alturas):
            # Cada barra respira con un desfase distinto: la onda parece moverse.
            oscilacion = ((desfase + indice * 2) % 8) * 4
            altura = altura_base + oscilacion - 16
            x = centro + (indice - 2) * 32
            lienzo.create_rectangle(
                x - 11, centro - altura / 2, x + 11, centro + altura / 2,
                fill=color, outline=borde, width=4,
            )

    def _dibujar_triangulo(self, lienzo, centro, color, borde) -> None:
        """ATENCION: triangulo con borde, la forma universal de mira esto."""
        lado = 146
        altura = lado * 0.87
        lienzo.create_polygon(
            centro, centro - altura / 2,
            centro - lado / 2, centro + altura / 2,
            centro + lado / 2, centro + altura / 2,
            fill=color, outline=borde, width=4,
        )
        lienzo.create_text(
            centro, centro + 18, text="!", fill=borde, font=("Segoe UI", 40, "bold"),
        )

    def _dibujar_reposo(self, lienzo, centro, borde) -> None:
        """REPOSO: circulo hueco, quieto y de borde punteado.

        El borde punteado no es un adorno: ESCUCHANDO tambien es un circulo, y en
        escala de grises los dos rellenos apagados se parecen demasiado. El punteado,
        el tamano menor y la ausencia de pulso hacen que se distingan sin depender del
        color.
        """
        radio = 44
        lienzo.create_oval(
            centro - radio, centro - radio, centro + radio, centro + radio,
            fill=PALETA["superficie_alta"], outline=borde, width=3, dash=(6, 5),
        )

    def _tomar_el_foco(self) -> None:
        """Trae la ventana al frente y le da el foco del teclado al abrirse.

        Sin esto, la ventana puede quedar detras de la terminal desde la que se lanzo.
        La aplicacion se ve, pero las teclas se las lleva la otra ventana y la barra
        espaciadora "no hace nada", sin ninguna pista de por que.
        """
        try:
            self.lift()
            self.focus_force()
        except Exception:  # noqa: BLE001 - tomar el foco nunca debe romper el arranque
            pass
