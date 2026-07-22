@echo off
chcp 65001 >nul
title Instalador de EpubReaderPro
color 0A

echo ============================================================
echo           INSTALADOR OFICIAL DE EPUBREADERPRO
echo ============================================================
echo.
echo Instalando EpubReaderPro en tu sistema...
echo.

set "TARGET_DIR=%LOCALAPPDATA%\EpubReaderPro_App"
set "SCRIPT_DIR=%~dp0"

echo [1/3] Creando directorio de instalación en:
echo       %TARGET_DIR%
echo.

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [2/3] Copiando archivos y dependencias...
xcopy "%SCRIPT_DIR%dist\EpubReaderPro\*" "%TARGET_DIR%\" /E /I /Y /Q >nul

echo [3/3] Creando accesos directos en el Escritorio y Menú Inicio...

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\EpubReaderPro.lnk'); $s.TargetPath = '%TARGET_DIR%\EpubReaderPro.exe'; $s.WorkingDirectory = '%TARGET_DIR%'; $s.Save()"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\EpubReaderPro.lnk'); $s.TargetPath = '%TARGET_DIR%\EpubReaderPro.exe'; $s.WorkingDirectory = '%TARGET_DIR%'; $s.Save()"

echo.
echo ============================================================
echo ¡INSTALACIÓN COMPLETADA CON ÉXITO!
echo.
echo Se han creado los accesos directos en tu Escritorio y Menú Inicio.
echo Ya puedes ejecutar EpubReaderPro en cualquier momento.
echo ============================================================
echo.
pause
