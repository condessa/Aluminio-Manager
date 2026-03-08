@echo off
title AluminioManager
echo Iniciando AluminioManager...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Verifique se Python e MySQL estao instalados.
    echo Consulte o ficheiro INSTALAR.md
    pause
)
