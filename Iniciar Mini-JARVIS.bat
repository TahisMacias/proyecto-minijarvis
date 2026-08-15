@echo off
rem ===================================================================
rem  Iniciar Mini-JARVIS con doble clic.
rem
rem  Hace tres cosas: se para en la carpeta del proyecto, comprueba que
rem  el entorno virtual y el archivo .env existan, y arranca la app.
rem
rem  Si algo falla, la ventana negra NO se cierra: se queda con el
rem  mensaje en pantalla para poder leerlo. Una ventana que aparece y
rem  desaparece en medio segundo no le sirve a nadie.
rem ===================================================================

title Mini-JARVIS

rem %~dp0 es la carpeta donde esta este archivo. Asi funciona sin importar
rem desde donde se ejecute, y se puede mover el proyecto de sitio.
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

if not exist ".env" (
    echo.
    echo  Falta el archivo .env con la clave de Together AI.
    echo.
    echo  Copia .env.example como .env y pon tu clave dentro.
    echo.
    pause
    exit /b 1
)

echo.
echo  Abriendo Mini-JARVIS...
echo  Esta ventana negra puede quedarse abierta detras. No la cierres:
echo  si la cierras, se cierra tambien el asistente.
echo.

".venv\Scripts\python.exe" main.py

rem Si la app termino con error, se hace una pausa para poder leerlo.
if errorlevel 1 (
    echo.
    echo  Mini-JARVIS se cerro con un error. El mensaje esta arriba.
    echo.
    pause
)
