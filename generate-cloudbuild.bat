@echo off
setlocal EnableDelayedExpansion

:: Configura aquí el ID de tu proyecto
set "PROJECT_ID=northern-hope-449920-t0"

:: Crear cloudbuild.yaml desde el template
(for /f "delims=" %%i in (cloudbuild.template.yaml) do (
    set "line=%%i"
    set "line=!line:{PROJECT_ID}=%PROJECT_ID%!"
    echo !line!
)) > "cloudbuild.yaml"

echo Archivo cloudbuild.yaml generado exitosamente para el proyecto %PROJECT_ID%
pause