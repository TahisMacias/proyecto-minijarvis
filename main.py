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
        from core.modo_local import (
            MotorConRespaldo,
            MotorLocal,
            TranscriptorConRespaldo,
            VozConRespaldo,
            hablar_local,
            precalentar_en_segundo_plano,
            transcribir_local,
        )
        from tools.manifest import MANIFIESTO
        from tools.system_skills import ejecutar_herramienta
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
    print(f"Herramientas: {len(MANIFIESTO)} disponibles "
          f"({', '.join(sorted(h['function']['name'] for h in MANIFIESTO))})")
    print("Abriendo la ventana...")

    memoria = MemoriaConversacional(
        system_prompt=SYSTEM_PROMPT,
        max_turnos=config.MAX_TURNOS_MEMORIA,
    )
    grabadora = GrabadoraDeVoz()

    # --- Modo sin internet (T-21) -------------------------------------------
    # Las tres piezas que hablan con la nube se envuelven con su equivalente local.
    # La nube sigue siendo el camino principal; lo local entra solo si falla por falta
    # de red. El orquestador recibe los envoltorios sin enterarse de que existen: por
    # eso esto no obliga a tocar ni una linea de core/orchestrator.py.
    #
    # Los modelos locales NO se cargan aqui. Se cargan la primera vez que hagan falta,
    # porque cuestan casi un minuto y casi nunca hacen falta.
    avisos_de_modo = []

    motor = MotorConRespaldo(
        MotorLLM(), MotorLocal(), avisar=avisos_de_modo.append)
    transcriptor = TranscriptorConRespaldo(
        transcribir, transcribir_local, avisar=avisos_de_modo.append)
    voz = VozConRespaldo(
        hablar, hablar_local, avisar=avisos_de_modo.append)

    # Los modelos locales se cargan YA, en segundo plano. Sin esto, el primer turno
    # sin internet tardaba mas de un minuto -18 s de Whisper, 37 s del modelo de
    # lenguaje- y durante todo ese rato la ventana solo decia "Pensando...". Un minuto
    # sin ninguna senal es indistinguible de estar colgado.
    print("Preparando el modo sin internet en segundo plano...")
    precalentar_en_segundo_plano(
        avisar=lambda _: avisos_de_modo.append(
            "Modo sin internet listo: si se cae la red, sigo funcionando."))

    # La ventana recibe una fabrica, no un orquestador ya hecho: solo ella sabe como
    # construir el puente `after(0, ...)` hacia su propio hilo, y ese puente es un
    # argumento obligatorio del orquestador.
    def crear_orquestador(notificar):
        return Orquestador(
            grabadora=grabadora,
            transcriptor=transcriptor,
            motor=motor,
            voz=voz,
            memoria=memoria,
            notificar=notificar,
            # Aqui es donde el Tool Calling entra en la aplicacion (T-15). El
            # orquestador ya sabia hacerlo desde T-09: recibe la lista de lo que se
            # puede pedir y la funcion que lo ejecuta. Hasta ahora se llamaba sin
            # estos dos argumentos, asi que respondia solo con texto.
            herramientas=MANIFIESTO,
            ejecutar_herramienta=ejecutar_herramienta,
            limite_rondas_tool=config.LIMITE_RONDAS_TOOL_CALLING,
            segundos_en_atencion=config.SEGUNDOS_EN_ATENCION,
        )

    # La ventana recibe tambien el motor y la memoria: los controles de
    # sustentacion (T-14) actuan sobre ellos -sliders sobre el motor, indicador de
    # turnos sobre la memoria- sin pasar por el orquestador, que ya estaba cerrado.
    aplicacion = AplicacionMiniJarvis(
        crear_orquestador, motor=motor, memoria=memoria, avisos_de_modo=avisos_de_modo)
    aplicacion.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
