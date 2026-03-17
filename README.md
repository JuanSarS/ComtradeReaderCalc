# COMTRADE Pro

**Herramienta profesional para análisis de fallas en sistemas de potencia usando archivos COMTRADE.**

---

## ⚡ Inicio Rápido

### Opción 1: Ejecutable (Recomendado)
```bash
ComtradeReaderCalc.exe
```
o haz doble clic en el archivo `.exe` en la carpeta raíz.

### Opción 2: Script Batch con Menú Interactivo
```bash
run_all_options.bat
```

### Opción 3: Línea de Comandos (Python Directo)
```bash
python src/main.py
```

---

## 📋 Requisitos Previos

- **Python 3.9+** (solo si ejecutas desde `python src/main.py`)
- **Windows** (arquitectura x64 para el ejecutable)
- **Espacio en disco**: ~200 MB

---

## 🔧 Instalación Paso a Paso

### 1️⃣ Descarga del Proyecto

Clona o descarga el repositorio:
```bash
git clone <tu-repo> ComtradeReaderCalc
cd ComtradeReaderCalc
```

### 2️⃣ (Opcional) Configurar Entorno Python

Si prefieres ejecutar desde código fuente:

**Crear entorno virtual:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Instalar dependencias:**
```bash
pip install -r requirements.txt
```

### 3️⃣ Ejecutar la Aplicación

**Usa el ejecutable (sin Python instalado):**
```bash
ComtradeReaderCalc.exe
```

**O el script interactivo:**
```bash
run_all_options.bat
```

---

## 🎯 Flujo Principal de Uso

1. **Cargar archivo COMTRADE**
   - Click en "Abrir COMTRADE" en la barra de herramientas
   - Selecciona archivo `.cfg`
   - El archivo `.dat` se carga automáticamente

2. **Explorar Señales**
   - Tab "Señales Instantáneas": visualiza formas de onda brutas y filtradas
   - Tab "RMS": análisis de valores eficaces

3. **Análisis Fasorial**
   - Tab "Fasores de Fase": diagramas fasoriales instantáneos
   - Tab "Fasores de Secuencia": componentes simétricas

4. **Análisis de Secuencia**
   - Tab "Componentes de Secuencia": descomposición de Fortescue
   - Identificación automática de tipos de falla

5. **Visualización Avanzada**
   - Tab "Baricentro Geométrico": trayectoria del triángulo de fases
   - Animación en tiempo real del centro de masa

6. **Generación de Reportes**
   - PDF con resultados completos del análisis
   - Tablas de valores numéricos detallados

---

## 📁 Estructura del Proyecto

```
ComtradeReaderCalc/
├── README.md                    # Este archivo (guía de inicio)
├── ComtradeReaderCalc.exe       # Ejecutable empaquetado
├── run_all_options.bat          # Script con menú interactivo
├── requirements.txt             # Dependencias Python
├── requirements-dev.txt         # Dependencias desarrollo (PyInstaller)
│
├── docs/                        # Documentación completa
│   ├── ARCHITECTURE.md          # Diseño de la aplicación
│   ├── QUICKSTART.md            # Guía rápida de inicio
│   ├── VISUAL_GUIDE.md          # Guía visual de UI
│   ├── PROJECT_SUMMARY.md       # Resumen del proyecto
│   └── MIGRATION.md             # Notas de migración
│
├── src/                         # Código fuente principal
│   ├── main.py                  # Punto de entrada (PyQt6)
│   ├── core/                    # Módulos de análisis
│   ├── gui/                     # Interfaz desktop
│   └── utils/                   # Utilidades
│
├── data/                        # Datos de ejemplo
├── tests/                       # Tests unitarios
└── .venv/                       # Entorno virtual (ignorado en git)
```

---

## 🚀 Scripts Disponibles

### `run_all_options.bat`
Menú interactivo con opciones:
1. **Ejecutar aplicación normal** - Abre la UI completa
2. **Ejecutar dashboard Dash** - Solo web UI (puerto 8050)
3. **Ejecutar PyQt6 Desktop** - Solo desktop con archivo cargado
4. **Test de importaciones** - Valida que todo está ok
5. **Test de análisis** - Ejecuta pipeline de análisis
6. **Ver logs** - Muestra último archivo de log
7. **Salir**

### `build_executable.py`
Regenera el ejecutable `.exe` si modificas código.

```bash
python build_executable.py
```

---

## 📊 Capacidades de Análisis

| Feature | Descripción |
|---------|-------------|
| **Lectura COMTRADE** | Parseo robusto de archivos .cfg/.dat IEEE C37.111 |
| **Filtrado adaptativo** | Band-pass 50/60 Hz con protección para baja sampling |
| **RMS deslizante** | Ventana de un ciclo, actualización progresiva |
| **Fasores DFT** | Cálculo fundamental y armónicos |
| **Fourier Transformada** | FFT para análisis de contenido armónico |
| **Componentes Simétricas** | Descomposición Fortescue (V0, V1, V2) |
| **Identificación Falla** | Clasificación automática (L-G, L-L, L-L-G, 3Φ) |
| **Triángulo Dinámico** | Visualización animada de trayectoria de fases |
| **Generación reportes** | PDF con análisis completo |

---

## 🛠️ Desarrollo

### Modificar y Recompilar

Si copias archivos `.py`:
```bash
pip install -r requirements-dev.txt
python build_executable.py
```

Esto regenera `ComtradeReaderCalc.exe` con tus cambios.

---

## 📞 Documentación Completa

Para información detallada, consulta la carpeta `docs/`:
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitectura técnica
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Guía paso a paso
- **[docs/VISUAL_GUIDE.md](docs/VISUAL_GUIDE.md)** - Referencia UI
- **[docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Resumen técnico

---

**Última actualización:** Marzo 2026
