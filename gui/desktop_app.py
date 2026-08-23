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

REDISENO T-19 (2026-08-23), pedido por la duena
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
    NOMBRE_ASISTENTE,
    PALETA,
    TEMPERATURA_MAXIMA,
    TEMPERATURA_PREDETERMINADA,
    TOP_P_PREDETERMINADO,
)
from core.orchestrator import Estado, TipoEvento


# --- Constantes de presentacion --------------------------------------------

# El PROYECTO se llama Mini-JARVIS (nombre de la tarea); la ASISTENTE se llama
# como diga config.NOMBRE_ASISTENTE, que es a quien le habla la usuaria. La barra
# de la ventana lleva los dos para que se entienda de un vistazo cual es cual.
TITULO = f"{NOMBRE_ASISTENTE} · Mini-JARVIS"

ANCHO_VENTANA = 1000          # dos columnas: el reactor y todo lo demas
# El diseno C apila conversacion, controles y laboratorio en una sola columna, asi
# que necesita mas alto que las versiones de tres columnas. Se subio de 720 a 790
# porque los botones del laboratorio quedaban cortados por el borde inferior: antes
# de eso se probo apretando margenes y alturas, y solo se gano ruido visual. Cuando
# el contenido no cabe, lo honesto es agrandar la ventana, no encoger el contenido.
# Sigue limitado por FRACCION_MAXIMA_DE_PANTALLA, asi que en una pantalla pequena se
# recorta solo.
ALTO_VENTANA = 790
FRACCION_MAXIMA_DE_PANTALLA = 0.88

MILIS_ANTIRREBOTE_ESPACIO = 60

LADO_LIENZO = 300             # la pieza protagonista del diseno C
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

    def __init__(self, crear_orquestador, motor=None, memoria=None,
                 avisos_de_modo=None) -> None:
        super().__init__()

        customtkinter.set_appearance_mode("dark")
        self.title(TITULO)
        self.geometry(f"{self._ancho_que_cabe()}x{self._alto_que_cabe()}")
        self.minsize(860, 620)
        self.configure(fg_color=PALETA["fondo_profundo"])

        # `motor` y `memoria` llegan para los controles de sustentacion (T-14): los
        # sliders necesitan un motor al que aplicarles el muestreo y el indicador
        # necesita una memoria que contar. Son opcionales para que la ventana se pueda
        # abrir sin ellos en una prueba.
        self._motor = motor
        self._memoria = memoria
        # Lista compartida con main.py: los envoltorios del modo local le anaden
        # un aviso cuando cambian de nube a local o al reves. Se vacia al leerla.
        self._avisos_de_modo = avisos_de_modo if avisos_de_modo is not None else []

        self._estado = Estado.REPOSO
        self._paso_animacion = 0
        self._espacio_presionado = False
        self._analisis_en_curso = False
        self._imagen_mapa = None
        self._imagen_superpuesta = None
        self._ruta_mapa_actual = None
        self._tokens_texto = ""
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
        """Maqueta la ventana: cabecera arriba, reactor a la izquierda, todo lo demas
        apilado a la derecha.

        DISENO C, "NEON MINIMO", elegido por la duena el 2026-08-23 entre tres bocetos
        dibujados. Las dos versiones anteriores se disenaron adivinando a partir de
        descripciones y las dos fallaron; esta se eligio mirando.

        LO QUE DEFINE ESTE DISENO ES LO QUE NO TIENE. No hay paneles con borde, ni
        cajas, ni recuadros dentro de recuadros: eso era lo que hacia que la ventana
        pareciera un formulario. Aqui solo hay fondo, lineas finas de separacion y
        texto, con una unica pieza protagonista a la izquierda.
        """
        self.configure(fg_color=PALETA["fondo_profundo"])
        self.grid_columnconfigure(0, weight=0, minsize=380)  # el reactor
        self.grid_columnconfigure(1, weight=1, minsize=430)  # todo lo demas
        self.grid_rowconfigure(1, weight=1)

        self._construir_cabecera()
        self._construir_columna_estado()
        self._construir_columna_derecha()

        self.bind_all("<KeyPress-space>", self._al_presionar_espacio)
        self.bind_all("<KeyRelease-space>", self._al_soltar_espacio)
        self.bind_all("<Escape>", lambda _e: self._cerrar_superposicion())
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        self._escribir(
            NOMBRE_ASISTENTE,
            f"Hola, soy {NOMBRE_ASISTENTE}. Soy una inteligencia artificial, asi que "
            "mis respuestas pueden contener errores. Manten presionado el boton y "
            "hablame.",
        )

    def _construir_cabecera(self) -> None:
        """Nombre arriba a la izquierda y una linea fina que cruza la ventana."""
        marco = customtkinter.CTkFrame(self, fg_color="transparent")
        marco.grid(row=0, column=0, columnspan=2, sticky="ew", padx=44, pady=(30, 0))
        marco.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(
            # El nombre va TAL CUAL, con su mayuscula. El resto de la ventana va en
            # minuscula por el diseno C, pero un nombre propio no es un rotulo: dejarlo
            # en minuscula lo convertia en una etiqueta mas.
            marco, text=NOMBRE_ASISTENTE, text_color=PALETA["texto_claro"],
            font=("Segoe UI", 26, "bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w")

        customtkinter.CTkLabel(
            marco, text="asistente de voz  ·  mini-jarvis",
            text_color=PALETA["texto_tenue"], font=("Segoe UI", 12), anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(0, 12))

        # Indicador de modo, arriba a la derecha. Un asistente que de pronto responde
        # peor y no explica por que es peor que uno que falla: si el respaldo local
        # entra, tiene que verse.
        self._indicador_modo = customtkinter.CTkLabel(
            marco, text="", text_color=PALETA["texto_tenue"],
            font=("Consolas", 11), anchor="e",
        )
        self._indicador_modo.grid(row=0, column=1, rowspan=2, sticky="e")
        marco.grid_columnconfigure(1, weight=0)

        # La linea separadora es un frame de 1 px de alto. En un diseno sin cajas es lo
        # unico que organiza la pantalla, asi que hace bastante trabajo para lo que es.
        linea = customtkinter.CTkFrame(marco, height=1, fg_color="#242430")
        linea.grid(row=2, column=0, sticky="ew")

    # --- Izquierda: la pieza protagonista --------------------------------------

    def _construir_columna_estado(self) -> None:
        marco = customtkinter.CTkFrame(self, fg_color="transparent")
        marco.grid(row=1, column=0, sticky="nsew", padx=(44, 24), pady=(14, 22))
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(0, weight=1)
        marco.grid_rowconfigure(3, weight=1)

        self._lienzo = tkinter.Canvas(
            marco, width=LADO_LIENZO, height=LADO_LIENZO,
            highlightthickness=0, bg=PALETA["fondo_profundo"],
        )
        self._lienzo.grid(row=1, column=0, pady=(0, 22))

        self._leyenda = customtkinter.CTkLabel(
            marco, text=LEYENDA_POR_ESTADO[Estado.REPOSO],
            text_color=PALETA["texto_claro"], font=("Segoe UI", 17), wraplength=300,
        )
        self._leyenda.grid(row=2, column=0, pady=(0, 20))

        # Boton de contorno, no relleno: en este diseno lo lleno pesa demasiado.
        self._boton = customtkinter.CTkButton(
            marco, text="manten presionado para hablar", height=58, corner_radius=29,
            fg_color="transparent", hover_color=PALETA["superficie"],
            text_color=PALETA["texto_claro"], font=("Segoe UI", 14),
            border_width=2, border_color=BORDE_REPOSO,
        )
        self._boton.grid(row=3, column=0, sticky="new", padx=26)
        self._boton.bind("<ButtonPress-1>", self._al_presionar)
        self._boton.bind("<ButtonRelease-1>", self._al_soltar)

        customtkinter.CTkLabel(
            marco, text="o la barra espaciadora",
            text_color=PALETA["texto_tenue"], font=("Segoe UI", 10),
        ).grid(row=4, column=0, pady=(10, 0))

    # --- Derecha: conversacion, controles y laboratorio, apilados ---------------

    def _construir_columna_derecha(self) -> None:
        marco = customtkinter.CTkFrame(self, fg_color="transparent")
        marco.grid(row=1, column=1, sticky="nsew", padx=(24, 44), pady=(14, 22))
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(1, weight=1, minsize=120)

        self._encabezado(marco, "conversacion").grid(row=0, column=0, sticky="w")

        self._conversacion = customtkinter.CTkTextbox(
            marco, fg_color=PALETA["superficie"], text_color=PALETA["texto_claro"],
            border_width=0, font=("Segoe UI", 13), wrap="word", corner_radius=10,
            height=130,
        )
        self._conversacion.grid(row=1, column=0, sticky="nsew", pady=(6, 16))
        self._conversacion.configure(state="disabled")

        self._construir_controles(marco).grid(row=2, column=0, sticky="ew")
        self._construir_laboratorio(marco).grid(row=3, column=0, sticky="ew", pady=(16, 0))

    def _construir_controles(self, contenedor):
        """Controles de sustentacion (T-14), sin caja que los encierre.

        No estan escondidos en un menu a proposito: la sustentacion consiste en
        ensenar el efecto de estos numeros en vivo, asi que tienen que estar a la vista
        y al lado de la conversacion sobre la que actuan.
        """
        marco = customtkinter.CTkFrame(contenedor, fg_color="transparent")
        marco.grid_columnconfigure(1, weight=1)

        self._encabezado(marco, "controles").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        customtkinter.CTkLabel(
            marco, text="modelo", text_color=PALETA["texto_tenue"],
            font=("Segoe UI", 12), anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(0, 14))

        self._selector_modelo = customtkinter.CTkOptionMenu(
            marco,
            values=[MODELO_LLM_PREDETERMINADO, MODELO_LLM_ALTERNO],
            command=self._cambiar_modelo,
            fg_color=PALETA["superficie"], button_color=PALETA["superficie_alta"],
            button_hover_color=PALETA["turquesa"], text_color=PALETA["texto_claro"],
            font=("Segoe UI", 11), dropdown_font=("Segoe UI", 11),
            corner_radius=8, height=30,
        )
        self._selector_modelo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=2)

        self._slider_temperatura, self._valor_temperatura = self._construir_slider(
            marco, fila=2, etiqueta="temperatura", minimo=0.0, maximo=TEMPERATURA_MAXIMA,
            inicial=TEMPERATURA_PREDETERMINADA, al_mover=self._cambiar_temperatura)

        self._slider_top_p, self._valor_top_p = self._construir_slider(
            marco, fila=3, etiqueta="top_p", minimo=0.1, maximo=1.0,
            inicial=TOP_P_PREDETERMINADO, al_mover=self._cambiar_top_p)

        # El indicador ocupa SU PROPIA FILA a lo ancho. Compartiendo fila con un boton
        # se quedaba sin sitio y se cortaba a media palabra: se leia "Memoria 1/10 · 20"
        # comiendose "tokens". Se intento acortando el texto y volvio a pasar en cuanto
        # la ventana se estrechaba: la causa no era el texto sino la celda.
        self._indicador_memoria = customtkinter.CTkLabel(
            marco, text="", text_color=PALETA["texto_tenue"], font=("Segoe UI", 11),
            anchor="w", justify="left", wraplength=460,
        )
        self._indicador_memoria.grid(row=4, column=0, columnspan=3, sticky="ew",
                                     pady=(10, 0))

        # El acceso al system prompt NO vive aqui: esta abajo, en la fila unica de
        # botones junto a los del laboratorio. La pantalla de la duena da 760 px utiles
        # y esta fila extra era justo lo que no cabia.
        return marco

    def _construir_slider(self, contenedor, fila, etiqueta, minimo, maximo,
                          inicial, al_mover):
        customtkinter.CTkLabel(
            contenedor, text=etiqueta, text_color=PALETA["texto_tenue"],
            font=("Segoe UI", 12), anchor="w",
        ).grid(row=fila, column=0, sticky="w", padx=(0, 14), pady=4)

        slider = customtkinter.CTkSlider(
            contenedor, from_=minimo, to=maximo, command=al_mover,
            fg_color=PALETA["superficie_alta"], progress_color=PALETA["turquesa"],
            button_color=PALETA["rosa"], button_hover_color=PALETA["texto_claro"],
            height=14, button_length=0, button_corner_radius=9,
        )
        slider.set(inicial)
        slider.grid(row=fila, column=1, sticky="ew", padx=(0, 14), pady=4)

        valor = customtkinter.CTkLabel(
            contenedor, text=f"{inicial:.2f}", text_color=PALETA["texto_claro"],
            font=("Consolas", 12), width=44, anchor="e",
        )
        valor.grid(row=fila, column=2, sticky="e", pady=4)
        return slider, valor

    def _construir_laboratorio(self, contenedor):
        """El laboratorio, visible a la vez que la conversacion.

        Muestra, sobre la ULTIMA frase que dijo la usuaria: como se corta en tokens y
        que numero le toca a cada uno, y el mapa de atencion de BETO para esa misma
        frase. Es la respuesta visual a la pregunta de sustentacion sobre tokenizacion
        y self-attention: no con un ejemplo de libro, sino con lo que se acaba de decir.

        Todo el calculo lo hace `exploration/transformer_lab.py`. Aqui no se
        reimplementa nada: si el laboratorio y esta seccion dijeran cosas distintas,
        una de las dos estaria mintiendo en la sustentacion.

        En este diseno el laboratorio se resume en dos lineas y el detalle se abre en
        la superposicion. La version anterior le daba una columna entera y quedaba
        vacia casi todo el rato.
        """
        marco = customtkinter.CTkFrame(contenedor, fg_color="transparent")
        marco.grid_columnconfigure(0, weight=1)

        self._encabezado(marco, "laboratorio").grid(row=0, column=0, sticky="w")

        self._laboratorio_frase = customtkinter.CTkLabel(
            marco, text="habla y aqui aparecera el analisis de lo que dijiste",
            text_color=PALETA["texto_tenue"], font=("Segoe UI", 11),
            wraplength=440, justify="left", anchor="w",
        )
        self._laboratorio_frase.grid(row=1, column=0, sticky="ew", pady=(6, 2))

        self._laboratorio_resumen = customtkinter.CTkLabel(
            marco, text="—", text_color=PALETA["texto_claro"],
            font=("Consolas", 12), anchor="w",
        )
        self._laboratorio_resumen.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        botones = customtkinter.CTkFrame(marco, fg_color="transparent")
        botones.grid(row=3, column=0, sticky="ew")

        customtkinter.CTkButton(
            botones, text="system prompt", width=130, height=34, corner_radius=17,
            fg_color="transparent", hover_color=PALETA["superficie"],
            text_color=PALETA["texto_tenue"], font=("Segoe UI", 12),
            border_width=1, border_color=PALETA["superficie_alta"],
            command=self._mostrar_system_prompt,
        ).pack(side="left", padx=(0, 10))

        self._boton_tokens = customtkinter.CTkButton(
            botones, text="ver los tokens", width=140, height=34, corner_radius=17,
            fg_color="transparent", hover_color=PALETA["superficie"],
            text_color=PALETA["turquesa"], font=("Segoe UI", 12),
            border_width=1, border_color=PALETA["turquesa"],
            command=self._abrir_superposicion_de_tokens, state="disabled",
        )
        self._boton_tokens.pack(side="left")

        self._boton_mapa = customtkinter.CTkButton(
            botones, text="mapa de atencion", width=160, height=34,
            corner_radius=17, fg_color="transparent", hover_color=PALETA["superficie"],
            text_color=PALETA["rosa"], font=("Segoe UI", 12),
            border_width=1, border_color=PALETA["rosa"],
            command=self._abrir_superposicion_del_mapa, state="disabled",
        )
        self._boton_mapa.pack(side="left", padx=(10, 0))

        return marco

    def _abrir_superposicion_de_tokens(self) -> None:
        """La tabla de tokens completa, que ya no cabe en la columna."""
        if not self._tokens_texto:
            return
        self._abrir_superposicion(
            "Como se corta en tokens tu ultima frase",
            constructor=lambda padre: self._caja_de_texto(
                padre, self._tokens_texto, mono=True),
        )

    def _encabezado(self, contenedor, texto):
        """Rotulo de seccion: minuscula, fino y con espaciado.

        En un diseno sin cajas, el rotulo es lo unico que separa una seccion de otra,
        asi que va tenue a proposito: tiene que ordenar sin llamar la atencion. El
        espaciado entre letras hace ese trabajo mejor que un tamano grande.
        """
        return customtkinter.CTkLabel(
            contenedor, text=" ".join(texto.lower()), text_color=PALETA["texto_tenue"],
            font=("Segoe UI", 10), anchor="w",
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
                texto = (f"Memoria {turnos}/{MAX_TURNOS_MEMORIA}  ·  {tokens} tokens\n"
                         "Ya descarta el turno mas antiguo.")
                color = PALETA["rosa"]
            else:
                # Corto a proposito. La version larga ("... turnos - N tokens aprox.")
                # se cortaba a media palabra en ventanas estrechas: se veia
                # "Memoria 2/10 turnc". Un indicador cortado no informa, confunde.
                texto = f"Memoria: {turnos} de {MAX_TURNOS_MEMORIA} turnos  ·  {tokens} tokens aprox."
                color = PALETA["texto_tenue"]
            self._indicador_memoria.configure(text=texto, text_color=color)
        self._revisar_modo()
        self.after(700, self._refrescar_indicador_de_memoria)

    def _revisar_modo(self) -> None:
        """Muestra si esta respondiendo la nube o el respaldo local.

        Los avisos los deja `core/modo_local` en una lista compartida. Se leen aqui y
        se vacian, para no repetir el mismo mensaje en cada latido.
        """
        while self._avisos_de_modo:
            self._escribir("Aviso", self._avisos_de_modo.pop(0), avisar=True)

        local = any(
            getattr(pieza, "usando_local", False)
            for pieza in (self._motor,) if pieza is not None
        )
        if local:
            self._indicador_modo.configure(
                text="◈ SIN INTERNET · modelo local",
                text_color=COLOR_BORDE_POR_ESTADO["ATENCION"])
        else:
            self._indicador_modo.configure(text="")

    def _mostrar_system_prompt(self) -> None:
        """Visor de solo lectura: lo que se le dice al modelo antes de cada turno."""
        from core.llm_engine import SYSTEM_PROMPT
        self._abrir_superposicion(
            "System prompt (solo lectura)",
            constructor=lambda padre: self._caja_de_texto(padre, SYSTEM_PROMPT),
        )

    def _caja_de_texto(self, padre, contenido: str, mono: bool = False):
        caja = customtkinter.CTkTextbox(
            padre, fg_color=PALETA["fondo_profundo"], text_color=PALETA["texto_claro"],
            font=("Consolas", 12) if mono else ("Segoe UI", 13),
            wrap="none" if mono else "word", border_width=0, corner_radius=12,
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
            self._escribir(NOMBRE_ASISTENTE, evento.texto)
        elif evento.tipo is TipoEvento.HERRAMIENTA:
            self._escribir("...", f"usando la herramienta {evento.texto}")
        elif evento.tipo is TipoEvento.ERROR:
            # El texto ya viene redactado para una persona: el orquestador se encarga
            # de que ninguna traza tecnica llegue hasta aqui. Va en ambar para que se
            # lea junto al triangulo del mismo color, no como dos cosas sueltas.
            self._escribir("Aviso", evento.texto, avisar=True)

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
        self._laboratorio_frase.configure(text=f'"{frase}"')

        # EL RESUMEN CABE EN UNA LINEA; EL DETALLE SE ABRE APARTE. La version anterior
        # dedicaba una columna entera a la tabla de tokens y estaba vacia casi todo el
        # rato: solo se llena despues de hablar. Aqui quedan los tres numeros que se
        # senalan en la sustentacion -cuantos tokens, la forma del tensor, cuantas
        # capas por cabezas- y la tabla completa se ve pulsando el boton.
        forma = resultado["forma"]
        self._laboratorio_resumen.configure(
            text=f"{len(resultado['filas'])} tokens   ·   {tuple(forma)}   ·   "
                 f"{resultado['n_capas']} capas x {resultado['n_cabezas']} cabezas"
        )

        lineas = [
            f"TOKENIZACION con el tokenizador real de Qwen  ->  "
            f"{len(resultado['filas'])} tokens",
            "",
            f"{'idx':>4}  {'ID':>9}  token",
            f"{'-' * 4}  {'-' * 9}  {'-' * 30}",
        ]
        lineas += [
            f"{indice:>4}  {id_token:>9}  {token}"
            for indice, id_token, token in resultado["filas"]
        ]
        lineas += [
            "",
            f"EMBEDDINGS de BETO: {tuple(forma)}",
            f"  = 1 frase, {forma[1]} tokens, {forma[2]} numeros por token",
            "",
            f"ATENCION: {resultado['n_capas']} capas x {resultado['n_cabezas']} cabezas",
        ]
        self._tokens_texto = "\n".join(lineas)
        self._boton_tokens.configure(state="normal")

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

    def _escribir(self, quien: str, texto: str, avisar: bool = False) -> None:
        """Escribe una linea en el panel de conversacion.

        `avisar` la pinta del MISMO ambar que el triangulo del estado ATENCION.

        No es decoracion. El mensaje de error sale en esta columna, el indicador de
        estado esta en la de al lado, y quien acaba de hablar mira el texto. Se
        comprobo con el mainloop real que el triangulo SI se dibujaba sus segundos
        completos, y la duena aun asi no lo vio dos veces seguidas: para cuando
        terminaba de leer el aviso, la figura ya habia vuelto a reposo. El color une
        las dos mitades del mismo aviso, el que se lee y el que se ve.
        """
        self._conversacion.configure(state="normal")
        inicio = self._conversacion.index("end-1c")
        self._conversacion.insert("end", f"{quien}: {texto}\n\n")
        if avisar:
            fin = self._conversacion.index("end-1c")
            self._conversacion.tag_add("aviso", inicio, fin)
            self._conversacion.tag_config(
                "aviso", foreground=COLOR_BORDE_POR_ESTADO["ATENCION"]
            )
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
        """Pinta el reactor HUD entero: cromo alrededor, figura del estado en el centro.

        EL CROMO Y LA SENAL SON COSAS DISTINTAS, y conviene no confundirlas al leer
        esto. Los anillos, las marcas y el barrido son **decoracion**: dan el aspecto
        de aparato encendido que pide la seccion 5.2 del enunciado ("interfaz visual
        tipo HUD") y que el criterio del 15 % premia como refuerzo de la identidad
        Jarvis. La **senal** sigue siendo la figura del centro, y sigue cumpliendo H-09:
        cuatro formas distintas, cuatro colores distintos. Si manana hubiera que quitar
        todo el cromo por rendimiento, la aplicacion seguiria siendo usable.
        """
        lienzo = self._lienzo
        lienzo.delete("all")

        color = COLOR_POR_ESTADO.get(self._estado.value, RELLENO_REPOSO)
        borde = COLOR_BORDE_POR_ESTADO.get(self._estado.value, BORDE_REPOSO)
        centro = LADO_LIENZO / 2

        # --- cromo ---
        self._dibujar_marco_hud(lienzo, borde)
        self._dibujar_anillos_hud(lienzo, centro, borde)
        self._dibujar_barrido(lienzo, centro, borde)

        # --- senal ---
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

    # --- Cromo del HUD ---------------------------------------------------------

    def _dibujar_marco_hud(self, lienzo, borde) -> None:
        """Cuatro escuadras en las esquinas, como una mira o un visor."""
        largo, margen = 26, 6
        lado = LADO_LIENZO
        esquinas = (
            ((margen, margen + largo), (margen, margen), (margen + largo, margen)),
            ((lado - margen - largo, margen), (lado - margen, margen),
             (lado - margen, margen + largo)),
            ((margen, lado - margen - largo), (margen, lado - margen),
             (margen + largo, lado - margen)),
            ((lado - margen - largo, lado - margen), (lado - margen, lado - margen),
             (lado - margen, lado - margen - largo)),
        )
        for puntos in esquinas:
            lienzo.create_line(
                *[c for punto in puntos for c in punto],
                fill=borde, width=2, capstyle="projecting",
            )

    def _dibujar_anillos_hud(self, lienzo, centro, borde) -> None:
        """Tres anillos concentricos girando a distinta velocidad, con marcas de dial.

        Todo esto es arte ORIGINAL generado por codigo. El repositorio es publico y no
        se sube ninguna imagen de terceros; lo unico que se toma prestado son dos
        colores, que no son propiedad de nadie.

        Los anillos giran en sentidos alternos y a velocidades distintas a proposito:
        con la misma velocidad el conjunto parece una sola pieza rigida, y es el
        desfase entre ellos lo que da la sensacion de mecanismo vivo.
        """
        paso = self._paso_animacion

        # Anillo exterior: marcas de dial, una larga cada cinco.
        radio = LADO_LIENZO / 2 - 20
        giro = paso * 0.6
        for indice in range(48):
            angulo = math.radians(indice * 7.5 + giro)
            largo = 9 if indice % 5 == 0 else 4
            cos_a, sen_a = math.cos(angulo), math.sin(angulo)
            lienzo.create_line(
                centro + cos_a * radio, centro + sen_a * radio,
                centro + cos_a * (radio - largo), centro + sen_a * (radio - largo),
                fill=borde, width=1,
            )

        # Anillo medio: tres arcos separados, girando al reves.
        radio_medio = radio - 16
        base = -paso * 1.4
        for sector in range(3):
            lienzo.create_arc(
                centro - radio_medio, centro - radio_medio,
                centro + radio_medio, centro + radio_medio,
                start=base + sector * 120, extent=76,
                style="arc", outline=borde, width=2,
            )

        # Anillo interior: dos arcos finos y rapidos, en el otro sentido.
        radio_interior = radio_medio - 13
        base = paso * 2.6
        for sector in range(2):
            lienzo.create_arc(
                centro - radio_interior, centro - radio_interior,
                centro + radio_interior, centro + radio_interior,
                start=base + sector * 180, extent=54,
                style="arc", outline=borde, width=1,
            )

    def _dibujar_barrido(self, lienzo, centro, borde) -> None:
        """Linea de barrido que gira, como el radar de una pantalla de control."""
        angulo = math.radians(self._paso_animacion * 3.2)
        radio = LADO_LIENZO / 2 - 22
        lienzo.create_line(
            centro, centro,
            centro + math.cos(angulo) * radio, centro + math.sin(angulo) * radio,
            fill=borde, width=1, dash=(3, 6),
        )

    # --- La senal: cuatro formas propias, mas la de reposo (H-09) --------------

    def _dibujar_circulo_con_pulso(self, lienzo, centro, color, borde) -> None:
        """ESCUCHANDO: circulo lleno que late despacio, como un microfono abierto."""
        fase = self._paso_animacion % 20
        radio = 40 + (fase if fase <= 10 else 20 - fase) * 1.4
        lienzo.create_oval(
            centro - radio, centro - radio, centro + radio, centro + radio,
            fill=color, outline=borde, width=5,
        )

    def _dibujar_puntos(self, lienzo, centro, color, borde) -> None:
        """PENSANDO: tres puntos que se encienden en secuencia, como quien delibera."""
        encendido = (self._paso_animacion // 4) % 3
        for indice in range(3):
            x = centro + (indice - 1) * 38
            radio = 19 if indice == encendido else 12
            lienzo.create_oval(
                x - radio, centro - radio, x + radio, centro + radio,
                fill=color if indice == encendido else PALETA["superficie"],
                outline=borde, width=4,
            )

    def _dibujar_onda(self, lienzo, centro, color, borde) -> None:
        """RESPONDIENDO: barras de distinta altura, la forma clasica de suena audio."""
        alturas = [26, 46, 66, 46, 26]
        desfase = self._paso_animacion // 2
        for indice, altura_base in enumerate(alturas):
            # Cada barra respira con un desfase distinto: la onda parece moverse.
            oscilacion = ((desfase + indice * 2) % 8) * 4
            altura = altura_base + oscilacion - 16
            x = centro + (indice - 2) * 27
            lienzo.create_rectangle(
                x - 9, centro - altura / 2, x + 9, centro + altura / 2,
                fill=color, outline=borde, width=3,
            )

    def _dibujar_triangulo(self, lienzo, centro, color, borde) -> None:
        """ATENCION: triangulo con borde, la forma universal de mira esto."""
        lado = 120
        altura = lado * 0.87
        lienzo.create_polygon(
            centro, centro - altura / 2,
            centro - lado / 2, centro + altura / 2,
            centro + lado / 2, centro + altura / 2,
            fill=color, outline=borde, width=4,
        )
        lienzo.create_text(
            centro, centro + 14, text="!", fill=borde, font=("Segoe UI", 34, "bold"),
        )

    def _dibujar_reposo(self, lienzo, centro, borde) -> None:
        """REPOSO: circulo hueco, quieto y de borde punteado.

        El borde punteado no es un adorno: ESCUCHANDO tambien es un circulo, y en
        escala de grises los dos rellenos apagados se parecen demasiado. El punteado,
        el tamano menor y la ausencia de pulso hacen que se distingan sin depender del
        color.
        """
        radio = 36
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
