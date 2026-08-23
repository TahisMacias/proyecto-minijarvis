# TESTING - v1.0 Entrega 27 de agosto

Solo checks humanos o no automatizables. Los gates deterministas viven en `AGENTS.md`
y en cada task brief de `PLAN_v1.0-entrega-27ago.md`.

La duena registra `[OK]`, `[FAIL: motivo]` o `[SKIP: motivo]` junto a la fecha.
Un fallo confirmado se convierte en una tarea para el Obrero, nunca en una edicion
directa de codigo desde este archivo.

## Fase 1 - Nucleo (limite 22 de agosto)

- [x] H-01. **[OK 2026-08-13]** Crear el venv e instalar el stack completo -> los 11
      paquetes instalan con wheels nativos `cp314` en Python 3.14.5. Exit code 0.
      Ninguno requirio compilacion ni version alternativa.
- [x] H-02. **[OK 2026-08-13]** Listar dispositivos de audio desde Python -> 10
      dispositivos de entrada. Predeterminado: "Microfono (Realtek(R) Audio)".
      Captura real de 0.5s a 16 kHz: 8000 frames, senal no nula.
- [x] H-03. **[OK 2026-08-14]** Entorno virtual limpio creado solo desde
      `requirements.txt`: los 16 imports funcionan, las pruebas pasan y todos los
      modulos cargan. Falta la version en OTRA maquina, que es parte de T-18.
- [x] H-04. **[OK 2026-08-14, firmado por la duena]** Uso real de la aplicacion con su
      propia voz: la captura sirvio y la transcripcion fue fiel.
- [x] H-05. **[OK 2026-08-14]** Frase real de la duena con acento local y un numero de
      cuatro digitos: "Cual es la raiz cuadrada de 3345" se transcribio exacta,
      digitos incluidos, que es la parte dificil.
- [x] H-06. **[OK 2026-08-14, prueba 3 del recorrido manual]** Tres turnos
      encadenados con referencia al anterior: mantuvo el hilo.
- [~] H-07. **[OK 2026-08-14 sobre la voz ANTERIOR]** La voz se entiende y suena
      natural. Se firmo con `es-MX-DaliaNeural`; despues fue `es-ES-XimenaNeural`.
      **La voz actual es `es-AR-ElenaNeural`** (2026-08-23), elegida por la duena
      escuchando seis muestras. La firma no se hereda: conviene volver a oirla dentro
      de la aplicacion, no solo en la muestra suelta.
- [x] H-08. **[OK 2026-08-14, prueba 4 del recorrido manual]** Mover, redimensionar y
      cambiar de pestana durante un turno: nunca aparecio "no responde".
- [x] H-09. **[OK 2026-08-14, firmado por la duena tras usar la aplicacion]** Apoyado
      ademas por medicion del lienzo: 4 colores distintos y 4 figuras distintas, mas una
      prueba automatica que falla si dos estados llegaran a compartir color.
- [?] H-10. Pedir a alguien ajeno al proyecto que use la app sin instrucciones -> logra
      completar un turno de conversacion.
      **CONTRADICCION ABIERTA (auditoria 2026-08-14).** En `docs/pruebas-manuales.md`
      la prueba 9.1, que es exactamente este check, esta marcada `[X]`. Aqui y en
      `CURRENT.md` figuraba como pendiente. No se firma en nombre de la duena: hace
      falta que ella diga cual de las dos es cierta. Si la persona ajena ya uso la
      aplicacion, H-10 se cierra; si no, sigue pendiente y es de los pocos checks que
      no se pueden improvisar el mismo dia.
- [?] H-11. Ejecutar `exploration/transformer_lab.py` -> imprime tokens, IDs, forma de
      embeddings y genera el PNG de atencion, legible para quien no vio el codigo.
      **Misma contradiccion**: las pruebas 8.1, 8.2 y 8.3 del recorrido manual estan
      marcadas `[X]`, incluida la de poder explicar la imagen en voz alta. Pendiente
      de que la duena lo confirme.
- [ ] H-12. Desconectar la red a mitad de un turno -> mensaje amable, la app sigue viva
      y acepta un turno nuevo al reconectar.
      **Equivalente automatico ya verificado (2026-08-14)**: con el motor apuntando a un
      puerto cerrado, un fallo de conexion REAL a mitad de turno produjo el aviso en
      lenguaje llano y la vuelta a REPOSO. Falta la version con el wifi apagado de verdad.

## Fase 2 - Valor agregado (limite 25 de agosto)

- [x] H-13. **[OK 2026-08-14, prueba 7 del recorrido manual]** T-13 quedo en APTO al
      aprobarse la Fase 2 el 2026-08-23. **Ya no hay pestana**: el laboratorio se ve a
      la vez que la conversacion (T-19), asi que este check queda cubierto por el H-09
      nuevo y por H-14.
- [ ] H-14. Poner `temperature` en 0.1, repetir una frase, subirla a 1.5 y repetirla ->
      la diferencia entre ambas respuestas es perceptible y explicable. Aprovechar para
      mirar el indicador de memoria y el selector de modelo en caliente.
- [x] H-15. **[OK 2026-08-23, firmado por la duena tras usar la aplicacion]** Las
      cuatro herramientas invocadas por voz, una por una:
      - `calcular` -> **57.79**, la pregunta que origino la herramienta. Resuelta.
      - `estado_laptop` -> porcentaje real de bateria.
      - `buscar_web` -> resultados reales.
      - `abrir_pagina` -> Wikipedia a pantalla completa, **tras corregir un defecto que
        encontro ella**: se construia `--kiosk=url` y Edge, para el que `--kiosk` es un
        interruptor sin valor, ignoraba la direccion y abria su pagina de inicio.
        Corregido en `d2b212a` y reprobado por ella.
      - Lista blanca -> pedirle Facebook **no abre nada** y lo dice con palabras.
- [ ] **H-09 BIS. Volver a firmar H-09 sobre la ventana nueva.** El tema cambio por
      completo de claro a oscuro: la firma del 2026-08-14 era sobre la ventana pastel y
      **no se puede reutilizar**. Mirar de lejos, sin leer el texto, y despues
      entrecerrando los ojos: ¿se distinguen los cuatro estados por color y por forma?

- [ ] H-19. **Modo sin internet (T-21).** Apagar el wifi y hablarle: debe avisar en
      ambar, responder con el modelo local y no caerse. **Hecho de facto por la duena el
      2026-08-23** -confirmo que funciona- pero sin marcarlo formalmente.
      Aviso para el video: NO preguntarle datos en este modo. A la misma pregunta sobre
      la capital de Ecuador contesto "Quito" una vez y "Santo Domingo" la otra. Con
      "quien eres" responde bien y demuestra lo mismo.

## Fase 3 - Cierre (26 y 27 de agosto)

- [ ] H-16. Leer el informe completo (borrador ya escrito en `docs/informe-tecnico.md`) -> se entiende sin haber visto el codigo, y ninguna
      afirmacion contradice lo que la aplicacion hace de verdad.
- [ ] H-17. Grabar y ver el video (guion listo en `docs/guion-video.md`) -> muestra el pipeline, los estados y la exploracion en 2-4 min,
      y sirve como respaldo si la demo en vivo falla.
- [ ] H-18. Instalar el proyecto desde el repositorio publico en **otra maquina** ->
      arranca siguiendo solo el README. Lo exige la seccion 6 del enunciado.

## Regresion

- [ ] R-01. Tras cerrar la Fase 2, repetir H-06 y H-12 -> las herramientas y los
      controles nuevos no rompieron la conversacion basica ni el manejo de errores.

## Results

- Date: 2026-08-14 (recorrido manual completo de la Fase 1 + auditoria de cierre)
- Environment: Windows 11 Pro 10.0.26200; **Python 3.14.5** fijado en T-01;
  venv en `.venv/`
- Verdict: Fase 1 tecnicamente completa. **9 checks firmados** (H-01 a H-09),
  **2 en contradiccion** por resolver (H-10, H-11), **1 con equivalente automatico
  verificado y la version manual pendiente** (H-12), y los de Fase 2 y 3 sin abrir.
- Failures mapped to tasks: los tres fallos del recorrido manual (pruebas 2.3, 5.1 y
  5.3) se corrigieron en los commits `88ac9b4` y `d688954`.
  **2.3 y 5.1 REPROBADAS POR LA DUENA el 2026-08-23 y pasan.** El circulo se ve verde
  al hablar, y pulsar sin decir nada ya no hace que el asistente conteste a "gracias":
  las dos correcciones funcionan en uso real, no solo en las pruebas.
  **5.3 sigue sin reprobar.** Es la unica que queda de la Fase 1, y es la que exige
  apagar el wifi de verdad.
