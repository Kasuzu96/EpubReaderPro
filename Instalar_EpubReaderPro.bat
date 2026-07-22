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

echo [1/3] Limpiando instalaciones previas...
if exist "%TARGET_DIR%" rmdir /s /q "%TARGET_DIR%"
mkdir "%TARGET_DIR%"

echo [2/3] Copiando archivos de la aplicacion...

if exist "%SCRIPT_DIR%EpubReaderPro.exe" goto COPY_CURRENT
if exist "%SCRIPT_DIR%EpubReaderPro_Instalador\EpubReaderPro.exe" goto COPY_SUBDIR
if exist "%SCRIPT_DIR%dist\EpubReaderPro\EpubReaderPro.exe" goto COPY_DIST

echo.
echo ============================================================
echo ERROR: No se encontro EpubReaderPro.exe en la carpeta.
echo.
echo Por favor asegurate de:
echo 1. Hacer clic derecho en EpubReaderPro_Instalador_Completo.zip
echo 2. Seleccionar 'Extraer todo...'
echo 3. Abrir la carpeta extraida y ejecutar Instalar_EpubReaderPro.bat
echo ============================================================
echo.
pause
exit /b 1

:COPY_CURRENT
xcopy "%SCRIPT_DIR%*" "%TARGET_DIR%\" /E /I /Y /Q >nul
goto CREATE_SHORTCUTS

:COPY_SUBDIR
xcopy "%SCRIPT_DIR%EpubReaderPro_Instalador\*" "%TARGET_DIR%\" /E /I /Y /Q >nul
goto CREATE_SHORTCUTS

:COPY_DIST
xcopy "%SCRIPT_DIR%dist\EpubReaderPro\*" "%TARGET_DIR%\" /E /I /Y /Q >nul
goto CREATE_SHORTCUTS

:CREATE_SHORTCUTS
echo [3/3] Creando accesos directos en Escritorio y Menu Inicio...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'EpubReaderPro.lnk')); $s.TargetPath = '%TARGET_DIR%\EpubReaderPro.exe'; $s.WorkingDirectory = '%TARGET_DIR%'; if (Test-Path '%TARGET_DIR%\app_icon.ico') { $s.IconLocation = '%TARGET_DIR%\app_icon.ico' }; $s.Save()"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Programs'), 'EpubReaderPro.lnk')); $s.TargetPath = '%TARGET_DIR%\EpubReaderPro.exe'; $s.WorkingDirectory = '%TARGET_DIR%'; if (Test-Path '%TARGET_DIR%\app_icon.ico') { $s.IconLocation = '%TARGET_DIR%\app_icon.ico' }; $s.Save()"

echo.
echo ============================================================
echo INSTALACION COMPLETADA CON EXITO!
echo.
echo Acceso directo creado en tu Escritorio y Menu Inicio.
echo Ya puedes ejecutar EpubReaderPro en cualquier momento.
echo ============================================================
echo.
pause
