"""Punto de entrada de Mini-JARVIS (tarea T-10).

    python main.py

Este archivo hace una sola cosa: armar las piezas y arrancar la ventana. Toda la
logica vive en `core/` y todo el dibujo en `gui/`. Aqui se ve, de un vistazo, como
encaja el sistema completo, que es justo lo que conviene poder mostrar en la
sustentacion.

Los fallos de arranque (falta la clave, no hay microfono) se atienden ANTES de abrir
la ventana y se explican en la consola. Abrir una interfaz que no puede funcionar
seria peor: la usuaria descubriria el problema recien al intentar hablar.
"""

from __future__ import annotations

import sys


def main() -> int:
    # Salida en UTF-8: sin esto los acentos de los mensajes pueden romperse cuando la
    # consola de Windows usa una codificacion heredada.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Los imports van dentro de la funcion a proposito: `config` valida la clave de
    # API al importarse, y queremos atrapar ese fallo aqui y explicarlo, en vez de
    # que Python vuelque una traza antes de que main() llegue a correr.
    try:
        import config
        from core.audio_capture import GrabadoraDeVoz, verificar_microfono
        from core.llm_engine import SYSTEM_PROMPT, MotorLLM
        from core.memory import MemoriaConversacional
        from core.orchestrator import Orquestador
        from core.stt_client import transcribir
        from core.tts_engine import hablar
        from gui.desktop_app import AplicacionMiniJarvis
    except Exception as excepcion:  # noqa: BLE001
        print(f"\nNo se pudo iniciar Mini-JARVIS.\n\n{excepcion}\n")
        return 1

    try:
        microfono = verificar_microfono()
        print(f"Microfono: {microfono}")
    except Exception as excepcion:  # noqa: BLE001
        print(f"\nNo se pudo iniciar Mini-JARVIS.\n\n{excepcion}\n")
        return 1

    print(f"Modelo: {config.MODELO_LLM_PREDETERMINADO}")
    print("Abriendo la ventana...")

    memoria = MemoriaConversacional(
        system_prompt=SYSTEM_PROMPT,
        max_turnos=config.MAX_TURNOS_MEMORIA,
    )
    motor = MotorLLM()
    grabadora = GrabadoraDeVoz()

    # La ventana recibe una fabrica, no un orquestador ya hecho: solo ella sabe como
    # construir el puente `after(0, ...)` hacia su propio hilo, y ese puente es un
    # argumento obligatorio del orquestador.
    def crear_orquestador(notificar):
        return Orquestador(
            grabadora=grabadora,
            transcriptor=transcribir,
            motor=motor,
            voz=hablar,
            memoria=memoria,
            notificar=notificar,
            limite_rondas_tool=config.LIMITE_RONDAS_TOOL_CALLING,
            segundos_en_atencion=config.SEGUNDOS_EN_ATENCION,
        )

    aplicacion = AplicacionMiniJarvis(crear_orquestador)
    aplicacion.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
