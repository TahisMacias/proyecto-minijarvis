"""Interfaz de escritorio de Mini-JARVIS (tarea T-10).

Ventana en CustomTkinter, modo claro, con la paleta pastel de `config.py`.

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
nada. Por eso cada estado tiene ademas su propia figura dibujada en un lienzo:
circulo lleno, tres puntos, onda y triangulo. La forma no es decoracion.
"""

from __future__ import annotations

import tempfile
import threading
import tkinter
from pathlib import Path

import customtkinter
from PIL import Image

from config import COLOR_POR_ESTADO, PALETA
from core.orchestrator import Estado, TipoEvento


# --- Constantes de presentacion --------------------------------------------

TITULO = "Mini-JARVIS"

ANCHO_VENTANA = 560
ALTO_VENTANA = 680
# Fraccion de la altura de pantalla que la ventana puede ocupar como maximo. El resto
# deja sitio a la barra de tareas y al marco de la ventana.
FRACCION_MAXIMA_DE_PANTALLA = 0.86

PESTANA_CONVERSACION = "Conversacion"
PESTANA_LABORATORIO = "Laboratorio"

# Margen que se espera antes de creerle a un "solte la barra espaciadora". Ver
# _al_presionar_espacio: por debajo de esto, un soltar+presionar es repeticion
# automatica del sistema, no un dedo humano.
MILIS_ANTIRREBOTE_ESPACIO = 60

LADO_LIENZO = 150          # el lienzo del indicador de estado es cuadrado
MILIS_ANIMACION = 90       # ritmo del pulso, los puntos y la onda

# Texto de cada estado. Es un APOYO: la forma y el color ya lo dicen todo para quien
# no puede o no alcanza a leer.
LEYENDA_POR_ESTADO = {
    Estado.REPOSO: "Listo. Manten presionado el boton para hablar.",
    Estado.ESCUCHANDO: "Te escucho...",
    Estado.PENSANDO: "Pensando...",
    Estado.RESPONDIENDO: "Respondiendo...",
    Estado.ATENCION: "Atencion",
}

# REPOSO no aparece en la tabla de la seccion 11 del diseno porque no es un estado de
# actividad. Se le da el gris del texto sobre el fondo crema: presente pero apagado,
# sin competir con los cuatro colores que si significan algo.
COLOR_REPOSO = PALETA["fondo_crema"]


class AplicacionMiniJarvis(customtkinter.CTk):
    """Ventana principal. Solo pinta y recoge pulsaciones; no piensa por su cuenta."""

    def __init__(self, crear_orquestador) -> None:
        super().__init__()

        customtkinter.set_appearance_mode("light")
        self.title(TITULO)
        self.geometry(f"{ANCHO_VENTANA}x{self._alto_que_cabe()}")
        self.minsize(460, 420)
        self.configure(fg_color=PALETA["fondo_crema"])

        self._estado = Estado.REPOSO
        self._paso_animacion = 0
        self._espacio_presionado = False
        self._analisis_en_curso = False
        self._imagen_mapa = None
        self._cierre_de_espacio_pendiente = None

        self._construir()

        # El orquestador se construye AQUI, pasandole el puente hacia el hilo
        # principal. Se recibe una funcion en vez del objeto ya hecho para que este
        # modulo sea el unico que decide como cruzar de hilo.
        self._orquestador = crear_orquestador(self._notificar_desde_otro_hilo)

        self._animar()

        # Que la ventana nazca con el foco del teclado: si nace detras de la terminal
        # que la lanzo, la barra espaciadora no le llega y parece que no funciona.
        self.after(120, self._tomar_el_foco)

    def _alto_que_cabe(self) -> int:
        """Altura de ventana que de verdad entra en esta pantalla.

        Windows suele venir con escalado al 125 % o al 150 %: una ventana declarada de
        680 se dibuja de 850 pixeles reales. En un portatil de 768 de alto, el boton
        de hablar terminaria debajo de la barra de tareas, invisible e inalcanzable, y
        la aplicacion pareceria rota sin estarlo. Se comprobo en esta maquina, con
        escalado 133 %.

        Por eso la altura no se fija a ciegas: se pregunta cuanta pantalla hay y
        cuanto la estan escalando, y se recorta si hace falta. Lo que se sacrifica es
        alto del panel de conversacion, que es la unica parte elastica de la ventana.
        """
        escala = customtkinter.ScalingTracker.get_window_scaling(self)
        alto_disponible = (self.winfo_screenheight() * FRACCION_MAXIMA_DE_PANTALLA) / escala
        return int(min(ALTO_VENTANA, alto_disponible))

    # --- Construccion de la ventana ----------------------------------------

    def _construir(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        titulo = customtkinter.CTkLabel(
            self,
            text=TITULO,
            text_color=PALETA["texto_gris_marengo"],
            font=("Segoe UI", 26, "bold"),
        )
        titulo.grid(row=0, column=0, pady=(22, 4))

        # --- Indicador de estado: lienzo (forma) + leyenda (texto de apoyo) ---
        marco_estado = customtkinter.CTkFrame(self, fg_color="transparent")
        marco_estado.grid(row=1, column=0, pady=(4, 10))

        self._lienzo = tkinter.Canvas(
            marco_estado,
            width=LADO_LIENZO,
            height=LADO_LIENZO,
            highlightthickness=0,
            bg=PALETA["fondo_crema"],
        )
        self._lienzo.pack()

        self._leyenda = customtkinter.CTkLabel(
            marco_estado,
            text=LEYENDA_POR_ESTADO[Estado.REPOSO],
            text_color=PALETA["texto_gris_marengo"],
            font=("Segoe UI", 14),
        )
        self._leyenda.pack(pady=(8, 0))

        # --- Pestanas: Conversacion y Laboratorio ----------------------------
        self._pestanas = customtkinter.CTkTabview(
            self,
            fg_color="white",
            segmented_button_selected_color=PALETA["azul_cielo"],
            segmented_button_selected_hover_color=PALETA["azul_cielo"],
            segmented_button_unselected_color=PALETA["fondo_crema"],
            text_color=PALETA["texto_gris_marengo"],
            corner_radius=12,
        )
        self._pestanas.grid(row=2, column=0, padx=24, pady=8, sticky="nsew")
        pestana_conversacion = self._pestanas.add(PESTANA_CONVERSACION)
        pestana_laboratorio = self._pestanas.add(PESTANA_LABORATORIO)
        self._pestanas.set(PESTANA_CONVERSACION)

        for pestana in (pestana_conversacion, pestana_laboratorio):
            pestana.grid_columnconfigure(0, weight=1)
            pestana.grid_rowconfigure(0, weight=1)

        self._conversacion = customtkinter.CTkTextbox(
            pestana_conversacion,
            fg_color="white",
            text_color=PALETA["texto_gris_marengo"],
            border_width=0,
            font=("Segoe UI", 13),
            wrap="word",
        )
        self._conversacion.grid(row=0, column=0, sticky="nsew")
        # Solo lectura, pero se escribe en el programaticamente: se habilita justo
        # para escribir y se vuelve a bloquear (ver _escribir).
        self._conversacion.configure(state="disabled")

        self._construir_laboratorio(pestana_laboratorio)

        # --- Boton de hablar --------------------------------------------------
        self._boton = customtkinter.CTkButton(
            self,
            text="Manten presionado para hablar",
            height=56,
            corner_radius=28,
            fg_color=PALETA["verde_menta"],
            hover_color=PALETA["azul_cielo"],
            text_color=PALETA["texto_gris_marengo"],
            font=("Segoe UI", 15, "bold"),
        )
        self._boton.grid(row=3, column=0, padx=24, pady=(8, 6), sticky="ew")

        # Push-to-talk de verdad: se atiende presionar y soltar, no el click completo.
        self._boton.bind("<ButtonPress-1>", self._al_presionar)
        self._boton.bind("<ButtonRelease-1>", self._al_soltar)

        self._pie = customtkinter.CTkLabel(
            self,
            text="La barra espaciadora hace lo mismo que el boton.",
            text_color=PALETA["texto_gris_marengo"],
            font=("Segoe UI", 11),
        )
        self._pie.grid(row=4, column=0, pady=(0, 14))

        # bind_all y no bind: con las pestanas, el foco del teclado puede acabar en
        # el selector, en el panel de texto o en el boton. `bind` en la ventana
        # depende de que el evento suba por la jerarquia; `bind_all` lo atiende
        # siempre, este donde este el foco.
        self.bind_all("<KeyPress-space>", self._al_presionar_espacio)
        self.bind_all("<KeyRelease-space>", self._al_soltar_espacio)
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        self._escribir(
            "Mini-JARVIS",
            "Hola. Soy una inteligencia artificial, asi que mis respuestas pueden "
            "contener errores. Manten presionado el boton y hablame.",
        )

    def _construir_laboratorio(self, contenedor) -> None:
        """Pestana Laboratorio (T-13): que le pasa por dentro al Transformer.

        Muestra, sobre la ULTIMA frase que dijo la usuaria: como se corta en tokens y
        que numero le toca a cada uno, y el mapa de atencion de BETO para esa misma
        frase. Es la respuesta visual a la pregunta de sustentacion sobre tokenizacion
        y self-attention: no con un ejemplo de libro, sino con lo que se acaba de decir.

        Todo el calculo lo hace `exploration/transformer_lab.py`. Aqui no se
        reimplementa nada: si el laboratorio y esta pestana dijeran cosas distintas,
        una de las dos estaria mintiendo en la sustentacion.
        """
        contenedor.grid_rowconfigure(0, weight=0)
        contenedor.grid_rowconfigure(1, weight=0)
        contenedor.grid_rowconfigure(2, weight=1)

        self._laboratorio_frase = customtkinter.CTkLabel(
            contenedor,
            text="Habla y aqui aparecera el analisis de lo que dijiste.",
            text_color=PALETA["texto_gris_marengo"],
            font=("Segoe UI", 12, "italic"),
            wraplength=440,
            justify="left",
        )
        self._laboratorio_frase.grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))

        self._laboratorio_tokens = customtkinter.CTkTextbox(
            contenedor,
            height=120,
            fg_color=PALETA["fondo_crema"],
            text_color=PALETA["texto_gris_marengo"],
            border_width=0,
            font=("Consolas", 12),
            wrap="none",
        )
        self._laboratorio_tokens.grid(row=1, column=0, sticky="ew", padx=8)
        self._laboratorio_tokens.configure(state="disabled")

        self._laboratorio_imagen = customtkinter.CTkLabel(
            contenedor,
            text="",
            image=None,
        )
        self._laboratorio_imagen.grid(row=2, column=0, sticky="n", padx=8, pady=8)

    # --- Entrada de la usuaria ---------------------------------------------

    def _al_presionar(self, evento=None) -> None:
        self._orquestador.empezar_a_escuchar()

    def _al_soltar(self, evento=None) -> None:
        self._orquestador.terminar_y_responder()

    def _al_presionar_espacio(self, evento=None) -> None:
        """Inicio de la escucha por teclado, a prueba de la repeticion automatica.

        EL PROBLEMA QUE RESUELVE ESTO: mientras una tecla sigue hundida, el sistema
        la repite. Segun la maquina, esa repeticion puede llegar como una ristra de
        KeyPress sueltos o como PAREJAS de soltar+presionar decenas de veces por
        segundo. En el segundo caso, mantener la barra espaciadora cerraba el
        microfono a los milisegundos de abrirlo: la usuaria hablaba y no se grababa
        nada. Ignorar solo el KeyPress repetido no bastaba, porque el que hacia dano
        era el KeyRelease falso.

        La solucion es no creerle a un KeyRelease de inmediato: se espera un instante
        y, si llega otro KeyPress en ese margen, era repeticion y se cancela el cierre.
        Un dedo humano no suelta y vuelve a presionar en 60 milisegundos; la
        repeticion automatica, si.
        """
        if self._cierre_de_espacio_pendiente is not None:
            # Habia un cierre agendado y llego otra pulsacion: era repeticion.
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

    # --- Puente entre hilos -------------------------------------------------

    def _notificar_desde_otro_hilo(self, evento) -> None:
        """Lo unico que el orquestador puede llamar. NO toca widgets: solo encola.

        `after` es seguro de llamar desde otro hilo; cualquier otra cosa de Tkinter
        no lo es. Esta funcion de dos lineas es toda la frontera entre los dos mundos.
        """
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
            self._escribir("...", f"consultando {evento.texto}")
        elif evento.tipo is TipoEvento.ERROR:
            # El texto ya viene redactado para una persona: el orquestador se encarga
            # de que ninguna traza tecnica llegue hasta aqui.
            self._escribir("Aviso", evento.texto)

    # --- Laboratorio (T-13) --------------------------------------------------

    def _analizar_en_segundo_plano(self, frase: str) -> None:
        """Lanza el analisis del Transformer en un hilo aparte.

        POR QUE UN HILO: la primera vez hay que cargar BETO, que son cientos de
        megabytes y varios segundos. Hacerlo en el hilo de la interfaz dejaria la
        ventana congelada justo despues de hablar, que es el momento en que la usuaria
        esta mirando. El criterio de aceptacion de T-13 lo dice explicitamente.

        Si ya hay un analisis corriendo, este se descarta: la frase nueva llegara con
        el siguiente turno y no vale la pena encolar trabajo que ya quedo viejo.
        """
        if self._analisis_en_curso:
            return
        self._analisis_en_curso = True
        self._laboratorio_frase.configure(
            text=f'Analizando: "{frase}"  (la primera vez tarda unos segundos)'
        )
        hilo = threading.Thread(
            target=self._analizar,
            args=(frase,),
            name="minijarvis-laboratorio",
            daemon=True,
        )
        hilo.start()

    def _analizar(self, frase: str) -> None:
        """Corre en el hilo del laboratorio. No toca ningun widget: solo calcula."""
        try:
            # Import perezoso a proposito: `transformer_lab` arrastra torch y
            # transformers, que tardan segundos en cargar y ocupan memoria. Si se
            # importara arriba, la aplicacion tardaria eso en abrir aunque nadie
            # llegue a mirar esta pestana.
            from exploration import transformer_lab

            filas = transformer_lab.tokenizar_con_qwen(frase)
            analisis = transformer_lab.analizar_con_beto(frase)
            ruta_png = Path(tempfile.gettempdir()) / "minijarvis-atencion.png"
            transformer_lab.dibujar_mapa_de_atencion(
                analisis["tokens"],
                analisis["atenciones"],
                transformer_lab.CAPA_ELEGIDA_BASE0,
                transformer_lab.CABEZA_ELEGIDA_BASE0,
                ruta_salida=ruta_png,
                silencioso=True,
            )
            resultado = {
                "frase": frase,
                "filas": filas,
                "forma": analisis["forma_embeddings"],
                "n_capas": analisis["n_capas"],
                "n_cabezas": analisis["n_cabezas"],
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

        self._laboratorio_frase.configure(text=f'Frase analizada: "{resultado["frase"]}"')

        lineas = [
            f"TOKENIZACION con el tokenizador real de Qwen  ->  {len(resultado['filas'])} tokens",
            "",
            f"{'idx':>4}  {'ID':>9}  token",
            f"{'-' * 4}  {'-' * 9}  {'-' * 24}",
        ]
        lineas += [
            f"{indice:>4}  {id_token:>9}  {token}"
            for indice, id_token, token in resultado["filas"]
        ]
        lineas += [
            "",
            f"EMBEDDINGS de BETO: {resultado['forma']}",
            f"  = (1 frase, {resultado['forma'][1]} tokens, {resultado['forma'][2]} numeros por token)",
            f"ATENCION: {resultado['n_capas']} capas x {resultado['n_cabezas']} cabezas.",
        ]

        self._laboratorio_tokens.configure(state="normal")
        self._laboratorio_tokens.delete("1.0", "end")
        self._laboratorio_tokens.insert("1.0", "\n".join(lineas))
        self._laboratorio_tokens.configure(state="disabled")

        self._mostrar_mapa(resultado["png"])

    def _mostrar_mapa(self, ruta_png) -> None:
        """Carga el PNG del mapa de atencion y lo encaja en el ancho disponible."""
        imagen = Image.open(ruta_png)
        ancho_disponible = max(self._laboratorio_imagen.winfo_width(), 400)
        proporcion = imagen.height / imagen.width
        ancho = min(ancho_disponible, 460)
        tamano = (ancho, int(ancho * proporcion))

        # Se guarda la referencia en el propio objeto: si se pierde, el recolector de
        # basura de Python se lleva la imagen y el widget queda en blanco. Es un
        # tropiezo clasico de Tkinter.
        self._imagen_mapa = customtkinter.CTkImage(light_image=imagen, size=tamano)
        self._laboratorio_imagen.configure(image=self._imagen_mapa, text="")

    # --- Pintado -------------------------------------------------------------

    def _cambiar_estado(self, estado: Estado) -> None:
        self._estado = estado
        self._paso_animacion = 0
        self._leyenda.configure(text=LEYENDA_POR_ESTADO.get(estado, ""))
        self._boton.configure(
            fg_color=COLOR_POR_ESTADO.get(estado.value, PALETA["verde_menta"])
        )

    def _escribir(self, quien: str, texto: str) -> None:
        self._conversacion.configure(state="normal")
        self._conversacion.insert("end", f"{quien}: {texto}\n\n")
        self._conversacion.see("end")
        self._conversacion.configure(state="disabled")

    # --- Animacion del indicador --------------------------------------------

    def _animar(self) -> None:
        """Redibuja la figura del estado actual y se vuelve a agendar.

        Se usa `after` en vez de un hilo: la animacion es trabajo de la interfaz y
        debe correr en su hilo, igual que todo lo demas que toca widgets.
        """
        self._paso_animacion += 1
        self._dibujar_estado()
        self.after(MILIS_ANIMACION, self._animar)

    def _dibujar_estado(self) -> None:
        lienzo = self._lienzo
        lienzo.delete("all")

        color = COLOR_POR_ESTADO.get(self._estado.value, COLOR_REPOSO)
        borde = PALETA["texto_gris_marengo"]
        centro = LADO_LIENZO / 2

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

    def _dibujar_circulo_con_pulso(self, lienzo, centro, color, borde) -> None:
        """ESCUCHANDO: circulo lleno que late despacio, como un microfono abierto."""
        # El radio oscila entre 40 y 52 px con un ciclo de 20 pasos (~1.8 s).
        fase = self._paso_animacion % 20
        radio = 40 + (fase if fase <= 10 else 20 - fase) * 1.2
        lienzo.create_oval(
            centro - radio, centro - radio, centro + radio, centro + radio,
            fill=color, outline=borde, width=2,
        )

    def _dibujar_puntos(self, lienzo, centro, color, borde) -> None:
        """PENSANDO: tres puntos que se encienden en secuencia, como quien delibera."""
        encendido = (self._paso_animacion // 4) % 3
        for indice in range(3):
            x = centro + (indice - 1) * 34
            radio = 17 if indice == encendido else 11
            lienzo.create_oval(
                x - radio, centro - radio, x + radio, centro + radio,
                fill=color if indice == encendido else PALETA["fondo_crema"],
                outline=borde, width=2,
            )

    def _dibujar_onda(self, lienzo, centro, color, borde) -> None:
        """RESPONDIENDO: barras de distinta altura, la forma clasica de "suena audio"."""
        alturas = [22, 40, 56, 40, 22]
        desfase = self._paso_animacion // 2
        for indice, altura_base in enumerate(alturas):
            # Cada barra respira con un desfase distinto: la onda parece moverse.
            oscilacion = ((desfase + indice * 2) % 8) * 3
            altura = altura_base + oscilacion - 12
            x = centro + (indice - 2) * 24
            lienzo.create_rectangle(
                x - 8, centro - altura / 2, x + 8, centro + altura / 2,
                fill=color, outline=borde, width=2,
            )

    def _dibujar_triangulo(self, lienzo, centro, color, borde) -> None:
        """ATENCION: triangulo con borde, la forma universal de "mira esto"."""
        lado = 108
        altura = lado * 0.87
        lienzo.create_polygon(
            centro, centro - altura / 2,
            centro - lado / 2, centro + altura / 2,
            centro + lado / 2, centro + altura / 2,
            fill=color, outline=borde, width=3,
        )
        lienzo.create_text(
            centro, centro + 14,
            text="!", fill=borde, font=("Segoe UI", 30, "bold"),
        )

    def _dibujar_reposo(self, lienzo, centro, borde) -> None:
        """REPOSO: circulo hueco, quieto y de borde punteado.

        El borde punteado no es un adorno: ESCUCHANDO tambien es un circulo, y en
        escala de grises el crema del reposo y el verde menta de la escucha se
        parecen demasiado. El punteado, el tamano menor y la ausencia de pulso hacen
        que los dos se distingan sin depender del color.
        """
        radio = 32
        lienzo.create_oval(
            centro - radio, centro - radio, centro + radio, centro + radio,
            fill=PALETA["fondo_crema"], outline=borde, width=2, dash=(6, 5),
        )

    def _tomar_el_foco(self) -> None:
        """Trae la ventana al frente y le da el foco del teclado al abrirse.

        Sin esto, la ventana puede quedar detras de la terminal desde la que se
        lanzo. La aplicacion se ve, pero las teclas se las lleva la otra ventana y la
        barra espaciadora "no hace nada", sin ninguna pista de por que.
        """
        try:
            self.lift()
            self.focus_force()
        except Exception:  # noqa: BLE001 - tomar el foco nunca debe romper el arranque
            pass
