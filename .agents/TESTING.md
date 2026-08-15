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
- [x] H-07. **[OK 2026-08-14, firmado por la duena]** La voz se entiende y suena
      natural. Voz `es-MX-DaliaNeural`, femenina, como se acordo.
- [x] H-08. **[OK 2026-08-14, prueba 4 del recorrido manual]** Mover, redimensionar y
      cambiar de pestana durante un turno: nunca aparecio "no responde".
- [x] H-09. **[OK 2026-08-14, firmado por la duena tras usar la aplicacion]** Apoyado
      ademas por medicion del lienzo: 4 colores distintos y 4 figuras distintas, mas una
      prueba automatica que falla si dos estados llegaran a compartir color.
- [ ] H-10. Pedir a alguien ajeno al proyecto que use la app sin instrucciones -> logra
      completar un turno de conversacion.
- [ ] H-11. Ejecutar `exploration/transformer_lab.py` -> imprime tokens, IDs, forma de
      embeddings y genera el PNG de atencion, legible para quien no vio el codigo.
- [ ] H-12. Desconectar la red a mitad de un turno -> mensaje amable, la app sigue viva
      y acepta un turno nuevo al reconectar.
      **Equivalente automatico ya verificado (2026-08-14)**: con el motor apuntando a un
      puerto cerrado, un fallo de conexion REAL a mitad de turno produjo el aviso en
      lenguaje llano y la vuelta a REPOSO. Falta la version con el wifi apagado de verdad.

## Fase 2 - Valor agregado (limite 25 de agosto)

- [~] H-13. **[OK 2026-08-14, prueba 7 del recorrido manual]** Verificado, pero la
      tarea T-13 tiene el veredicto en suspenso hasta el OK de la duena.
      Abrir la pestana Laboratorio tras hablar -> muestra los tokens y el mapa de
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
