@echo off
title Instalador Oficial de EpubReaderPro
color 0A

echo ============================================================
echo           INSTALADOR OFICIAL DE EPUBREADERPRO
echo ============================================================
echo.
echo Instalando EpubReaderPro en tu sistema...
echo.

set TARGET_DIR=%LOCALAPPDATA%\EpubReaderPro_App
set SCRIPT_DIR=%~dp0

echo [1/3] Creando directorio de instalacion...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [2/3] Copiando archivos y dependencias de la aplicacion...

if exist "%SCRIPT_DIR%dist\EpubReaderPro\EpubReaderPro.exe" (
    xcopy "%SCRIPT_DIR%dist\EpubReaderPro\*" "%TARGET_DIR%\" /E /I /Y /Q >nul
) else if exist "%SCRIPT_DIR%EpubReaderPro.exe" (
    xcopy "%SCRIPT_DIR%*" "%TARGET_DIR%\" /E /I /Y /Q >nul
) else (
    echo ERROR: No se encontro EpubReaderPro.exe en la carpeta del instalador.
    pause
    exit /b 1
)

echo [3/3] Creando accesos directos con icono oficial...

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\EpubReaderPro.lnk'); $s.TargetPath = '%TARGET_DIR%\EpubReaderPro.exe'; $s.WorkingDirectory = '%TARGET_DIR%'; if (Test-Path '%TARGET_DIR%\app_icon.ico') { $s.IconLocation = '%TARGET_DIR%\app_icon.ico' }; $s.Save()"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\EpubReaderPro.lnk'); $s.TargetPath = '%TARGET_DIR%\EpubReaderPro.exe'; $s.WorkingDirectory = '%TARGET_DIR%'; if (Test-Path '%TARGET_DIR%\app_icon.ico') { $s.IconLocation = '%TARGET_DIR%\app_icon.ico' }; $s.Save()"

echo.
echo ============================================================
echo INSTALACION COMPLETADA CON EXITO!
echo.
echo Acceso directo creado en tu Escritorio y Menu Inicio.
echo Ya puedes ejecutar EpubReaderPro en cualquier momento.
echo ============================================================
echo.
pause
