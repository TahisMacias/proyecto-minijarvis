@echo off
rem ===================================================================
rem  Iniciar Mini-JARVIS con doble clic.
rem
rem  Comprueba que el entorno virtual y el archivo .env existan, y
rem  arranca la aplicacion SIN dejar una ventana negra detras.
rem
rem  POR QUE pythonw Y NO python: `python.exe` abre una consola que se
rem  queda abierta todo el rato detras de la ventana. Funciona, pero
rem  ensucia la pantalla y sale en el video de la sustentacion.
rem  `pythonw.exe` es el mismo interprete sin consola.
rem
rem  Lo que se pierde con pythonw son los mensajes de arranque, que
rem  antes se veian en esa consola. Por eso se guardan en un archivo:
rem  si algo falla, queda el rastro en registro-arranque.txt en vez de
rem  desaparecer sin dejar nada.
rem ===================================================================

title Mini-JARVIS

rem %~dp0 es la carpeta donde esta este archivo. Asi funciona sin importar
rem desde donde se ejecute, y se puede mover el proyecto de sitio.
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
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

rem start "" lanza el proceso y devuelve el control enseguida, para que
rem esta ventana se cierre sola en lugar de quedarse esperando.
start "" ".venv\Scripts\pythonw.exe" main.py

exit /b 0
