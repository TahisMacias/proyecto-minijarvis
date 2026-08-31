@echo off
rem ===================================================================
rem  Abre el laboratorio del Transformer con doble clic.
rem
rem  POR QUE EXISTE ESTE ARCHIVO: escribir el comando a mano falla de
rem  dos formas, y las dos pasaron. Primera: si la consola no esta en
rem  la carpeta del proyecto, Python no encuentra el paquete
rem  `exploration` y aborta. Segunda: aunque la carpeta sea la correcta,
rem  el `python` del sistema NO tiene torch ni transformers instalados,
rem  porque las dependencias viven en el entorno virtual del proyecto.
rem
rem  Este archivo resuelve las dos: se situa en su propia carpeta y usa
rem  el interprete de .venv. Es el que hay que usar en la sustentacion.
rem ===================================================================

title Laboratorio del Transformer - Mini-JARVIS

rem %~dp0 es la carpeta donde esta este archivo. Asi funciona sin
rem importar desde donde se ejecute, y se puede mover el proyecto.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  No se encontro el entorno virtual en la carpeta .venv
    echo.
    echo  Falta instalarlo. Abre PowerShell en esta carpeta y ejecuta:
    echo.
    echo      python -m venv .venv
    echo      .venv\Scripts\Activate.ps1
    echo      pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo  Cargando el laboratorio. La primera vez tarda: descarga los
echo  modelos de Hugging Face. Despues arranca en unos segundos.
echo.

".venv\Scripts\python.exe" -m exploration.transformer_lab

rem La pausa es lo que hace util este archivo en una sustentacion: sin
rem ella la ventana se cierra al terminar y la salida, que es el
rem entregable, desaparece antes de poder leerla.
echo.
echo  ============================================================
echo   Terminado. Desplaza hacia arriba para ver todo.
echo   Cierra esta ventana cuando quieras.
echo  ============================================================
pause >nul
