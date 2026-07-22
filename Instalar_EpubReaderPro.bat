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

echo [1/4] Limpiando instalaciones previas...
if exist "%TARGET_DIR%" rmdir /s /q "%TARGET_DIR%"
mkdir "%TARGET_DIR%"

echo [2/4] Buscando archivos de la aplicacion...

set SOURCE_DIR=

if exist "%SCRIPT_DIR%EpubReaderPro.exe" (
    set "SOURCE_DIR=%SCRIPT_DIR%"
) else if exist "%SCRIPT_DIR%EpubReaderPro_Instalador\EpubReaderPro.exe" (
    set "SOURCE_DIR=%SCRIPT_DIR%EpubReaderPro_Instalador\"
) else if exist "%SCRIPT_DIR%dist\EpubReaderPro\EpubReaderPro.exe" (
    set "SOURCE_DIR=%SCRIPT_DIR%dist\EpubReaderPro\"
) else if exist "%USERPROFILE%\Downloads\EpubReaderPro_Instalador_Completo.zip" (
    echo Descomprimiendo automaticamente paquete desde Descargas...
    powershell -Command "Expand-Archive -Path '%USERPROFILE%\Downloads\EpubReaderPro_Instalador_Completo.zip' -DestinationPath '%TARGET_DIR%' -Force"
    set "SOURCE_DIR=%TARGET_DIR%\EpubReaderPro_Instalador\"
)

if exist "%SOURCE_DIR%EpubReaderPro.exe" (
    echo [3/4] Copiando archivos a %TARGET_DIR%...
    xcopy "%SOURCE_DIR%*" "%TARGET_DIR%\" /E /I /Y /Q >nul
) else if exist "%TARGET_DIR%\EpubReaderPro.exe" (
    echo Archivos descomprimidos con exito.
) else (
    echo.
    echo ============================================================
    echo ATENCION: Debes DESCOMPRIMIR (Extraer) el archivo ZIP completo
    echo antes de ejecutar el instalador.
    echo.
    echo PASOS SENCILLOS:
    echo 1. Haz clic derecho en 'EpubReaderPro_Instalador_Completo.zip'
    echo 2. Selecciona 'Extraer todo...'
    echo 3. Abre la carpeta extraida y ejecuta 'Instalar_EpubReaderPro.bat'
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo [4/4] Creando accesos directos con icono oficial...

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\EpubReaderPro.lnk'); $s.TargetPath = '%TARGET_DIR%\EpubReaderPro.exe'; $s.WorkingDirectory = '%TARGET_DIR%'; if (Test-Path '%TARGET_DIR%\app_icon.ico') { $s.IconLocation = '%TARGET_DIR%\app_icon.ico' }; $s.Save()"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\EpubReaderPro.lnk'); $s.TargetPath = '%TARGET_DIR%\EpubReaderPro.exe'; $s.WorkingDirectory = '%TARGET_DIR%'; if (Test-Path '%TARGET_DIR%\app_icon.ico') { $s.IconLocation = '%TARGET_DIR%\app_icon.ico' }; $s.Save()"

echo.
echo ============================================================
echo ¡INSTALACION COMPLETADA CON EXITO!
echo.
echo Acceso directo creado en tu Escritorio y Menu Inicio.
echo Ya puedes ejecutar EpubReaderPro en cualquier momento.
echo ============================================================
echo.
pause
