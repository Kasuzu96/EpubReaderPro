@echo off
title Lector EPUB Pro
cd /d "%~dp0"
echo Iniciando Lector de Libros EPUB...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error al iniciar la aplicacion. Verifique que Python este instalado.
    pause
)
