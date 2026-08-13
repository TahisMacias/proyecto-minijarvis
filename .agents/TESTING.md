# TESTING - v0.1 Fundamentos

Solo checks humanos o no automatizables. Los gates deterministas viven en AGENTS.md
y en cada task brief. La duena registra `[OK]`, `[FAIL: motivo]` o `[SKIP: motivo]`.
Un fallo confirmado se convierte en una tarea, no en una edicion directa de codigo.

## Release blockers

- [ ] H-01. Crear `.venv` e instalar el stack -> toda libreria instala sin error,
      o queda documentado exactamente cual falla y por que.
- [ ] H-05. Abrir el repositorio publico en el navegador -> no aparece ningun `.env`,
      ninguna API key ni dato personal. Se revisa archivo por archivo.

## Changed behavior

- [ ] H-02. Seguir el README desde cero en una carpeta limpia -> el proyecto queda
      instalado sin pasos no documentados. Idealmente en otra maquina; el PDF lo exige.
- [ ] H-03. Ejecutar `exploration/transformer_lab.py` -> imprime tokens, IDs, shape de
      embeddings y la matriz de atencion, de forma legible para alguien que no vio el codigo.
- [ ] H-04. Leer `docs/propuesta-tecnica.md` en voz alta -> se entiende en una pagina
      y sirve como guion base para la sustentacion.

## Regression

- (sin flujos previos que romper; el proyecto arranca en esta version)

## Results

- Date: pendiente
- Environment: Windows 11 Pro 10.0.26200, Python 3.14.5
- Verdict: pending
- Failures mapped to tasks: ninguno todavia
