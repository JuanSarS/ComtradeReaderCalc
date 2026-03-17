@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: COMTRADE Pro - Menu de Ejecución Interactivo
:: ============================================================================
:: Este script proporciona múltiples opciones para ejecutar la aplicación
:: COMTRADE Pro de diferentes maneras.
:: ============================================================================

:menu_main
cls
echo.
echo ============================================================================
echo   COMTRADE PRO - Menu Principal
echo ============================================================================
echo.
echo   [1] Ejecutar Aplicacion Normal (Desktop + Dashboard)
echo   [2] Ejecutar Solo Dashboard Web (Dash en puerto 8050)
echo   [3] Ejecutar Solo Desktop (PyQt6)
echo   [4] Validar Importaciones de Modulos
echo   [5] Ejecutar Tests de Analisis
echo   [6] Limpiar Archivos Temporales y Cache
echo   [7] Instalar/Actualizar Dependencias
echo   [8] Compilar Ejecutable (.exe)
echo   [9] Abrir Carpeta del Proyecto
echo   [0] Salir
echo.
echo ============================================================================

set /p option="Selecciona una opcion [0-9]: "

if "%option%"=="1" goto option_1
if "%option%"=="2" goto option_2
if "%option%"=="3" goto option_3
if "%option%"=="4" goto option_4
if "%option%"=="5" goto option_5
if "%option%"=="6" goto option_6
if "%option%"=="7" goto option_7
if "%option%"=="8" goto option_8
if "%option%"=="9" goto option_9
if "%option%"=="0" goto exit_script

echo.
echo ERROR: Opcion no valida. Intenta nuevamente.
echo.
timeout /t 2 /nobreak
goto menu_main

:: ============================================================================
:: OPCION 1: Ejecutar Aplicacion Normal
:: ============================================================================
:option_1
cls
echo.
echo [1] EJECUTANDO APLICACION NORMAL
echo  - Desktop PyQt6 + Dashboard Dash integrado
echo  - Se cargará la interfaz completa
echo.
echo Iniciando en 2 segundos...
timeout /t 2 /nobreak

cd /d "%~dp0"

:: Verificar que existe el directorio src
if not exist "src\main.py" (
    echo ERROR: src\main.py no encontrado
    echo Verifica que estés en el directorio correcto del proyecto
    pause
    goto menu_main
)

:: Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo.
echo ▶ Iniciando aplicacion...
echo.
python src\main.py

if errorlevel 1 (
    echo.
    echo ✗ La aplicacion se cerro con error
    echo.
) else (
    echo.
    echo ✓ Aplicacion cerrada exitosamente
    echo.
)

pause
goto menu_main

:: ============================================================================
:: OPCION 2: Ejecutar Solo Dashboard Web
:: ============================================================================
:option_2
cls
echo.
echo [2] EJECUTANDO DASHBOARD WEB (SOLO)
echo  - Se abrira un servidor Dash en http://localhost:8050
echo  - Abre tu navegador en esa direccion
echo  - Presiona Ctrl+C para detener el servidor
echo.
echo Iniciando en 2 segundos...
timeout /t 2 /nobreak

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo.
echo ▶ Iniciando servidor Dash...
echo  URL: http://localhost:8050
echo  Presiona Ctrl+C para detener
echo.

python -c "from src.ui.web.app import create_dash_app; app = create_dash_app(); app.run_server(debug=True, port=8050)"

echo.
pause
goto menu_main

:: ============================================================================
:: OPCION 3: Ejecutar Solo PyQt6 Desktop
:: ============================================================================
:option_3
cls
echo.
echo [3] EJECUTANDO SOLO DESKTOP (PYQT6)
echo  - Se abrira la ventana desktop sin dashboard integrado
echo  - Interfaz nativa de PyQt6
echo.
echo Iniciando en 2 segundos...
timeout /t 2 /nobreak

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo.
echo ▶ Iniciando aplicacion PyQt6...
echo.

python -c "from src.gui.main_window import MainWindow; from PyQt6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())"

if errorlevel 1 (
    echo.
    echo ✗ Error al ejecutar desktop
    echo.
) else (
    echo.
    echo ✓ Desktop cerrado
    echo.
)

pause
goto menu_main

:: ============================================================================
:: OPCION 4: Validar Importaciones
:: ============================================================================
:option_4
cls
echo.
echo [4] VALIDANDO IMPORTACIONES DE MODULOS
echo.
echo ▶ Comprobando que todos los modulos esten instalados...
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python -c "
import sys
modules_to_test = [
    'PyQt6',
    'PyQt6.QtWebEngineWidgets',
    'numpy',
    'scipy',
    'pandas',
    'plotly',
    'dash',
    'dash_bootstrap_components',
]

print('Probando importaciones...\n')
all_ok = True
for mod in modules_to_test:
    try:
        __import__(mod)
        print(f'  ✓ {mod}')
    except ImportError as e:
        print(f'  ✗ {mod} - NO ENCONTRADO')
        all_ok = False

print()
if all_ok:
    print('✓ TODAS LAS IMPORTACIONES OK')
    sys.exit(0)
else:
    print('✗ FALTAN IMPORTACIONES')
    print('  Ejecuta: pip install -r requirements.txt')
    sys.exit(1)
"

if errorlevel 1 (
    echo.
    echo ✗ Faltan dependencias. Instalalas con:
    echo    pip install -r requirements.txt
    echo.
) else (
    echo.
    echo ✓ Todos los modulos estan disponibles
    echo.
)

pause
goto menu_main

:: ============================================================================
:: OPCION 5: Test de Analisis
:: ============================================================================
:option_5
cls
echo.
echo [5] EJECUTANDO TESTS DE ANALISIS
echo.
echo ▶ Verificando pipeline de analisis COMTRADE...
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

if exist "tests\test_comtrade_reader.py" (
    python -m pytest tests\test_comtrade_reader.py -v
) else (
    echo ▶ Test manual de importacion y pipeline...
    python -c "
from src.core.comtrade_reader import ComtradeReader
from src.core.analysis_pipeline import AnalysisPipeline
print('✓ Modulos de analisis importados exitosamente')
"
)

if errorlevel 1 (
    echo.
    echo ✗ Error en tests
    echo.
) else (
    echo.
    echo ✓ Tests completados
    echo.
)

pause
goto menu_main

:: ============================================================================
:: OPCION 6: Limpiar Cache
:: ============================================================================
:option_6
cls
echo.
echo [6] LIMPIANDO ARCHIVOS TEMPORALES
echo.

cd /d "%~dp0"

echo ▶ Eliminando carpetas de cache...

if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo  ✓ __pycache__
)

if exist "src\__pycache__" (
    rmdir /s /q src\__pycache__
    echo  ✓ src\__pycache__
)

if exist "src\core\__pycache__" (
    rmdir /s /q src\core\__pycache__
    echo  ✓ src\core\__pycache__
)

if exist "src\gui\__pycache__" (
    rmdir /s /q src\gui\__pycache__
    echo  ✓ src\gui\__pycache__
)

if exist "dash_app\__pycache__" (
    rmdir /s /q dash_app\__pycache__
    echo  ✓ dash_app\__pycache__
)

if exist ".pytest_cache" (
    rmdir /s /q .pytest_cache
    echo  ✓ .pytest_cache
)

if exist "dist" (
    rmdir /s /q dist
    echo  ✓ dist (construccion anterior)
)

if exist "build" (
    rmdir /s /q build
    echo  ✓ build (construccion anterior)
)

echo.
echo ✓ Limpieza completada
echo.

pause
goto menu_main

:: ============================================================================
:: OPCION 7: Instalar Dependencias
:: ============================================================================
:option_7
cls
echo.
echo [7] INSTALAR/ACTUALIZAR DEPENDENCIAS
echo.
echo Opciones:
echo  [A] Instalar dependencias base (requirements.txt)
echo  [B] Instalar dependencias desarrollo (requirements-dev.txt)
echo  [C] Volver
echo.

set /p suboption="Selecciona [A/B/C]: "

if /i "%suboption%"=="A" goto install_base
if /i "%suboption%"=="B" goto install_dev
if /i "%suboption%"=="C" goto menu_main

goto menu_main

:install_base
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
echo.
echo ▶ Instalando requirements.txt...
pip install -r requirements.txt
echo.
echo ✓ Instalacion completada
pause
goto menu_main

:install_dev
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
echo.
echo ▶ Instalando requirements-dev.txt...
pip install -r requirements-dev.txt
echo.
echo ✓ Instalacion completada (incluye PyInstaller)
pause
goto menu_main

:: ============================================================================
:: OPCION 8: Compilar Ejecutable
:: ============================================================================
:option_8
cls
echo.
echo [8] COMPILANDO EJECUTABLE (.exe)
echo.
echo Esto creara ComtradeReaderCalc.exe en la carpeta raiz
echo  - Requiere PyInstaller (instala con opcion [7B])
echo  - Tomara entre 1-5 minutos segun tu PC
echo.
echo Continuar? [S/N]

set /p confirm="Respuesta: "

if /i "%confirm%"=="N" goto menu_main

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo.
echo ▶ Iniciando compilacion (esto puede tomar unos minutos)...
echo.

python build_executable.py

if errorlevel 1 (
    echo.
    echo ✗ Error durante la compilacion
    echo.
) else (
    echo.
    echo ✓ Ejecutable creado exitosamente: ComtradeReaderCalc.exe
    echo.
    echo Ahora puedes ejecutar: ComtradeReaderCalc.exe
    echo.
)

pause
goto menu_main

:: ============================================================================
:: OPCION 9: Abrir Carpeta del Proyecto
:: ============================================================================
:option_9
start explorer "%~dp0"
goto menu_main

:: ============================================================================
:: Salida
:: ============================================================================
:exit_script
echo.
echo ¡Hasta luego!
echo.
exit /b 0
