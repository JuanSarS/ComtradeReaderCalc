# 📚 Documentación - COMTRADE Pro

Bienvenido a la documentación técnica y de usuario de **COMTRADE Pro**. Esta carpeta contiene todos los materiales necesarios para entender, usar y desarrollar la aplicación.

---

## 🚀 Comienza Aquí

### Para Usuarios Finales

1. **[README.md](../README.md)** (en raíz)
   - Guía de inicio rápido
   - Instrucciones de instalación
   - Cómo ejecutar la aplicación

2. **[QUICKSTART.md](QUICKSTART.md)** 
   - Paso a paso detallado
   - Primeros pasos en la aplicación
   - Flujos comunes de trabajo

3. **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)**
   - Diagrama de flujo de datos
   - Descripción de cada tab/vista
   - Explicación de gráficas

---

## 💻 Para Desarrolladores

### Arquitectura y Diseño

- **[ARCHITECTURE.md](ARCHITECTURE.md)**
  - Arquitectura de 3 capas (Desktop + Web + Core)
  - Descripción de módulos principales
  - Data flow y patrones de comunicación
  - Algoritmos matemáticos implementados

### Resumen del Proyecto

- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**
  - Estructura completa del proyecto
  - Estado de implementación
  - Checklist de features
  - Fases de desarrollo

### Notas de Migración

- **[MIGRATION.md](MIGRATION.md)**
  - Cambios recientes en la arquitectura
  - Deprecaciones y refactoring
  - Compatibilidad con versiones previas

---

## 📊 Componentes Principales

### Módulos de Análisis (`src/core/`)

| Módulo | Propósito | Estado |
|--------|-----------|--------|
| `comtrade_reader.py` | Lectura de archivos COMTRADE IEEE C37.111 | ✅ Completo |
| `signal_filter.py` | Filtrado digital adaptativo (50/60 Hz) | ✅ Completo |
| `rms_calculator.py` | Cálculo RMS con ventana deslizante | ✅ Completo |
| `phasor_calculator.py` | Análisis fasorial (DFT) | ✅ Completo |
| `symmetrical_components.py` | Componentes simétricas (Fortescue) | ✅ Completo |
| `triangle_analyzer.py` | Análisis geométrico del triángulo | ✅ Completo |

### Interface de Usuario

| Componente | Tecnología | Estado |
|-----------|-----------|--------|
| Desktop Shell | PyQt6 + QWebEngineView | ✅ Operativo |
| Dashboard Web | Dash + Plotly | ✅ Operativo |
| Visualizaciones | Plotly graphs | ✅ Animadas |
| Reportes | PDF generation | ✅ Funcional |

---

## 🔧 Configuración y Compilación

### Requisitos de Desarrollo

Ver: `requirements-dev.txt`
```bash
pip install -r requirements-dev.txt
```

### Compilar Ejecutable

```bash
python build_executable.py
```

Esto genera `ComtradeReaderCalc.exe` empaquetado con PyInstaller.

### Scripts Disponibles

- `run_all_options.bat` - Menú interactivo con múltiples opciones
- `build_executable.py` - Compilador PyInstaller

---

## 📖 Guías Rápidas

### Estructura de Directorios

```
ComtradeReaderCalc/
├── docs/                    # Esta carpeta (documentación)
│   ├── README.md           # Índice (este archivo)
│   ├── ARCHITECTURE.md     # Documentación técnica
│   ├── QUICKSTART.md       # Guía de primer uso
│   ├── VISUAL_GUIDE.md     # Guía visual
│   ├── PROJECT_SUMMARY.md  # Resumen del proyecto
│   └── MIGRATION.md        # Notas de migración
│
├── src/                     # Código principal
│   ├── main.py            # Punto de entrada
│   ├── core/              # Módulos de análisis
│   ├── gui/               # Interfaz desktop
│   └── utils/             # Utilidades
│
├── data/                    # Datos de ejemplo
├── tests/                   # Tests unitarios
├── README.md               # Guía principal (raíz)
├── run_all_options.bat     # Menú interactivo
└── build_executable.py     # Script de compilación
```

---

## 🎓 Capacidades Técnicas

### Lectura COMTRADE
- IEEE C37.111-1991, 1999, 2013
- Formato ASCII y binario
- Múltiples tasas de muestreo
- Validación robusta de datos

### Procesamiento de Señales
- Filtrado adaptativo Butterworth
- Detección automática de frecuencia fundamental
- RMS deslizante (ventana de 1 ciclo)
- Protección para archivos de bajo muestreo

### Análisis Fasorial
- Transformada DFT en frecuencia fundamental
- Cálculo de magnitud y ángulo
- Análisis de armónicos
- Seguimiento dinámico con cursor

### Componentes Simétricas
- Transformación Fortescue
- Secuencias V0, V1, V2 (e I0, I1, I2)
- Cálculo de desbalance
- Identificación automática de tipo de falla

### Visualización
- Gráficos interactivos Plotly
- Animación progresiva de trayectoria
- Diagramas fasoriales polares
- Triángulo de fases dinámico

---

## 🤝 Contribución

Para modificar o mejorar la documentación:

1. Edita los archivos `.md` en esta carpeta
2. Sigue el formato Markdown estándar
3. Incluye ejemplos de código cuando sea relevante
4. Actualiza este índice si agregas nuevos archivos

---

## 📝 Historial de Cambios

### Versión 2.1 (Marzo 2026 - Actualización)
- ✅ Animación progresiva de trayectoria mejorada (500ms, cubic-in-out)
- ✅ Documentación reorganizada en carpeta `docs/`
- ✅ README principal simplificado y enfocado en users
- ✅ Script `run_all_options.bat` con menú completo (9 opciones)
- ✅ Build script `build_executable.py` con PyInstaller
- ✅ requirements-dev.txt para dependencias de desarrollo

### Versión 2.0 (Febrero 2026)
- ✅ Cursor-driven phasors y sequence RMS
- ✅ Steady-state text results
- ✅ Global cursor workflow + persistent filtering
- ✅ Triangle + barycenter animation
- ✅ COMTRADE parser robustness improvements
- ✅ Dash callback fixes

### Versión 1.0 (Febrero 2026)
- ✅ Arquitectura base implementada
- ✅ Módulos de análisis completados
- ✅ UI Dash + PyQt6 integrada
- ✅ Reportes PDF generados

---

## 📞 Soporte

Para dudas o reportes de problemas:
- Consulta el archivo correspondiente en esta carpeta
- Revisa los archivos de código fuente (bien documentados con docstrings)
- Ejecuta los tests: `pytest tests/`

---

**Última actualización:** Marzo 2026

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
cd src
python main.py
```

The command launches a local PyQt6 window and loads the embedded dashboard inside the application.

### Basic Workflow

1. **Open File**: Click `Open COMTRADE` in the desktop toolbar and select a `.cfg` file
2. **Inspect Results**: Use the embedded dashboard views for signals, RMS, phasors and sequence components
3. **Iterate Locally**: The web UI remains inside the desktop window; no external browser is opened
4. **Generate Reports**: Continue using the Python reporting modules as the reporting flow is consolidated

### Tabs Overview

- **Instantaneous Signals**: View raw voltage and current waveforms
- **RMS Signals**: Analyze RMS trends with sliding window
- **Phasors**: View phasor diagrams and magnitude/angle tables
- **Sequence Components**: Analyze symmetrical components and identify fault type
- **Triangle Visualization**: Examine phase triangle geometry and barycenter motion
- **Report**: Generate and export PDF reports

## Project Structure

```
ComtradeReaderCalc/
├── Src/core/analysis/                # Shared engineering and orchestration layer
├── Src/ui/desktop/                # Native PyQt shell and embedded web host
├── Src/ui/web/                     # Embedded Dash app factory and shared state
├── Src/ui/pages/                   # Existing Dash views kept as compatibility layer
├── src/                        # Legacy desktop GUI and original modules
├── tests/                      # Unit tests
├── data/                       # Sample COMTRADE files
└── requirements.txt
```

## Architecture

The application now follows a desktop-shell architecture:

- **Desktop Layer**: PyQt6 window, toolbar, native dialogs and embedded QWebEngineView
- **Web UI Layer**: Dash + Plotly scientific interface rendered locally inside the desktop shell
- **Core Engine Layer**: COMTRADE parsing, filtering, RMS, phasors, symmetrical components and report generation

All analysis modules remain independent of the UI, allowing for:
- Easy testing and validation
- Future migration to a richer React client if needed
- Reusable engineering services for other frontends

## Development Status

**Current Version**: 1.0.0 (Architecture and Skeleton)

This release provides:
- ✓ Complete project structure
- ✓ Class skeletons with comprehensive docstrings
- ✓ GUI layout and tab organization
- ✓ Architecture ready for implementation

**Next Steps**: Implement mathematical algorithms and plotting logic in TODO sections

## Technical Details

### Signal Processing
- **RMS Calculation**: One-cycle sliding window (configurable: centered, forward, backward)
- **Phasor Calculation**: Discrete Fourier Transform at fundamental frequency
- **Filtering**: Butterworth band-pass filter centered at system frequency

### Symmetrical Components
- **Transformation Matrix**: Fortescue's method with 'a' operator
- **Imbalance Factors**: (V2/V1) and (V0/V1) percentages
- **Fault Identification**: Pattern matching on sequence magnitudes

### Triangle Analysis
- **Barycenter**: Centroid of three phasor vertices
- **Properties**: Area, perimeter, side lengths, asymmetry factor
- **Animation**: Linear interpolation between states

## For Developers

### Adding New Features

1. Core processing: Add modules in `Src/core/analysis/`
2. GUI components: Add tabs in `(legacy)tabs/`
3. Follow existing class structure and docstring style
4. Update this README with new capabilities

### Testing

```bash
# Run tests (when implemented)
pytest tests/
```

### Packaging for Distribution

```bash
# Using PyInstaller (embedded desktop build)
pyinstaller --onefile --windowed Src/main.py
```

## Engineering Notes

### COMTRADE Standard Compliance
- IEEE C37.111-1991, 1999, 2013
- Supports both analog and digital channels
- Handles multiple sampling rates

### Power System Conventions
- Phasor angles in degrees (0-360° or ±180°)
- RMS values for magnitude representation
- Three-phase ABC sequence
- Positive sequence rotation: counter-clockwise

### Coordinate Systems
- Phasor diagrams: Complex plane (real, imaginary)
- Phase angles: Referenced to phase A (typically 0°)
- Symmetrical components: Zero, positive, negative sequence

## License

Academic/Educational Use

## Authors

Power Systems Protection Engineering Team

## Support

For issues, questions, or contributions, please refer to the course materials or contact the development team.

---

**Note**: This application is designed for educational and professional use in power system protection engineering. Always validate results against known test cases before using for critical applications.
