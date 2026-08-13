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
- [ ] H-03. Seguir el README desde cero en una carpeta limpia -> el proyecto queda
      instalado sin ningun paso que no este escrito.
- [ ] H-04. Grabar 5 segundos y reproducir lo capturado -> se escucha la voz con claridad,
      sin cortes ni saturacion.
- [ ] H-05. Transcribir una frase en espanol con acento local -> el texto devuelto es
      fiel. Probar tambien una frase con un termino tecnico.
- [ ] H-06. Conversar 3 turnos encadenados con referencias al turno anterior -> el
      asistente mantiene el hilo y su personalidad es consistente.
- [ ] H-07. Escuchar la voz sintetizada -> se entiende, la entonacion es natural y el
      genero de la voz es el acordado.
- [ ] H-08. Durante un turno, mover y redimensionar la ventana -> la interfaz responde
      en todo momento; nunca aparece "no responde".
- [ ] H-09. Observar los 4 estados sin leer texto -> se distinguen solo por color y forma.
- [ ] H-10. Pedir a alguien ajeno al proyecto que use la app sin instrucciones -> logra
      completar un turno de conversacion.
- [ ] H-11. Ejecutar `exploration/transformer_lab.py` -> imprime tokens, IDs, forma de
      embeddings y genera el PNG de atencion, legible para quien no vio el codigo.
- [ ] H-12. Desconectar la red a mitad de un turno -> mensaje amable, la app sigue viva
      y acepta un turno nuevo al reconectar.

## Fase 2 - Valor agregado (limite 25 de agosto)

- [ ] H-13. Abrir la pestana Laboratorio tras hablar -> muestra los tokens y el mapa de
      atencion de lo que se acaba de decir, sin congelar la ventana.
- [ ] H-14. Poner `temperature` en 0.1, repetir una frase, subirla a 1.5 y repetirla ->
      la diferencia entre ambas respuestas es perceptible y explicable.
- [ ] H-15. Pedir por voz las tres herramientas, una por una -> cada una se invoca y
      responde. Intentar abrir un dominio fuera de la lista blanca -> se rechaza.

## Fase 3 - Cierre (26 y 27 de agosto)

- [ ] H-16. Leer el informe completo -> se entiende sin haber visto el codigo, y ninguna
      afirmacion contradice lo que la aplicacion hace de verdad.
- [ ] H-17. Ver el video -> muestra el pipeline, los estados y la exploracion en 2-4 min,
      y sirve como respaldo si la demo en vivo falla.
- [ ] H-18. Instalar el proyecto desde el repositorio publico en **otra maquina** ->
      arranca siguiendo solo el README. Lo exige la seccion 6 del enunciado.

## Regresion

- [ ] R-01. Tras cerrar la Fase 2, repetir H-06 y H-12 -> las herramientas y los
      controles nuevos no rompieron la conversacion basica ni el manejo de errores.

## Results

- Date: 2026-08-13 (parcial: H-01, H-02)
- Environment: Windows 11 Pro 10.0.26200; **Python 3.14.5** fijado en T-01;
  venv en `.venv/`
- Verdict: pending (16 de 18 checks por ejecutar)
- Failures mapped to tasks: ninguno
