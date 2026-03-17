@echo off
REM ============================================================================
REM COMTRADE Pro - Ejecutable Directo
REM ============================================================================
REM Simple launcher que ejecuta ComtradeReaderCalc.exe
REM
REM Si el .exe no existe aun, ofrece compilarlo o proporciona instrucciones
REM ============================================================================

setlocal enabledelayedexpansion

cd /d "%~dp0"

if exist "ComtradeReaderCalc.exe" (
    REM Ejecutar directamente
    start ComtradeReaderCalc.exe
    exit /b 0
) else (
    REM El .exe no existe
    cls
    echo.
    echo ============================================================================
    echo   COMTRADE Pro - Ejecutable No Encontrado
    echo ============================================================================
    echo.
    echo El archivo ComtradeReaderCalc.exe no existe aun.
    echo.
    echo Opciones:
    echo.
    echo [1] Compilar ahora (requiere PyInstaller)
    echo [2] Usar menu interactivo: run_all_options.bat
    echo [3] Ejecutar desde Python (requiere Python instalado)
    echo [4] Salir
    echo.
    
    set /p choice="Elige una opcion [1-4]: "
    
    if "%choice%"=="1" (
        echo.
        echo Compilando ejecutable...
        if exist "build_executable.py" (
            python build_executable.py
            if errorlevel 0 (
                start ComtradeReaderCalc.exe
            )
        ) else (
            echo ERROR: build_executable.py no encontrado
            pause
        )
        exit /b 0
    )
    
    if "%choice%"=="2" (
        call run_all_options.bat
        exit /b 0
    )
    
    if "%choice%"=="3" (
        python src\main.py
        exit /b 0
    )
    
    exit /b 0
)
