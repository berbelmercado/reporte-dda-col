# Reporte DDA Colombia — Automatización de Descarga y Persistencia

Sistema de automatización ETL que extrae el reporte de vehículos entregados por concesionarios a clientes finales (reporte DDA) desde un portal web, y persiste la información estructurada en una base de datos SQL Server para su uso en reportería y análisis operacional.

---

## ¿Qué hace este proyecto?

Automatiza un proceso que anteriormente requería acceso manual al portal web de SOFASA, descarga del reporte, y carga manual de datos. El sistema realiza el ciclo completo de forma desatendida:

1. **Autenticación y navegación web** mediante Selenium en el portal de reportes
2. **Descarga del reporte DDA** (vehículos entregados por concesionarios)
3. **Procesamiento y transformación** de los datos con Pandas
4. **Persistencia en SQL Server** para disponibilidad en reportería downstream
5. **Empaquetado como ejecutable** para despliegue en servidores Windows sin Python
6. **Generación de log** Para seguimiento en caso de errores
---

## Arquitectura

El proyecto aplica una arquitectura en capas con separación clara de responsabilidades. Cada capa tiene una única función y se comunica únicamente con las capas adyacentes.

---

## Flujo de datos

1. **main.py**
   - Llama a `etl_dda_controlador.procesar_reporte_dda()`

2. **Descarga del archivo**
   - Hasta N intentos con `ClienteSelenium.descargar_archivo_dda()`
   - Pasos:
     - Login en SPOTFIRE (IPN + clave)
     - Navegación por carpetas: `DA3 → DESING → COL → REPORTS → IN PROGRESS → DDA`
     - Context-click → Exportar → Descargar archivo Excel
   - Retorna:
     - `{"estado": True}` si éxito
     - `{"estado": False, "error": "..."}` si falla

3. **Procesamiento del archivo**
   - `ProcesarArchivo.leer_modificar_archivo()`
     - Valida que el archivo no esté vacío
     - Lee Excel con Pandas → filtra `Process == "Delivery"`

4. **Inserción en base de datos**
   - `InsertaDatos.conexion_sql()` → pyodbc → SQL Server (ODBC Driver 17)
   - `InsertaDatos.insertar_datos(dataframe)`
     - `INSERT INTO reporte_dda_temp (VIN, End_Date)`
     - Delta: `INSERT INTO reporte_dda WHERE vin NOT IN reporte_dda`
     - `DELETE reporte_dda_temp`

5. **Post-proceso**
   - Elimina el archivo Excel descargado

---

## Utilidades transversales
- **Logger**: activo en todas las capas → escribe en archivo `.log`
- **Resolver rutas**: activo en todas las capas → compatibilidad `.py` / `.exe`


## Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| **Python 3.x** | Lenguaje principal |
| **Selenium** | Automatización del navegador y descarga del reporte |
| **Pandas** | Transformación y procesamiento del archivo descargado |
| **pyodbc** | Conexión y persistencia en SQL Server |
| **webdriver-manager** | Gestión automática del ChromeDriver |
| **python-dotenv** | Configuración segura mediante variables de entorno |
| **PyInstaller** | Generación de ejecutable `.exe` para producción |

---

## ⚙️ Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/berbelmercado/reporte-dda-col.git
cd reporte-dda-col
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requerimientos.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Credenciales del portal web
PORTAL_URL=https://portal.sofasa.com
PORTAL_USER=tu_usuario
PORTAL_PASSWORD=tu_contraseña

# SQL Server
DB_SERVER=tu_servidor
DB_NAME=tu_base_de_datos
DB_USER=usuario_db
DB_PASSWORD=contraseña_db
```

>  El archivo `.env` está excluido por `.gitignore`. Nunca lo subas al repositorio.
>  Crear la carpeta Log
>  Crear la carpeta Recursos
### 4. Ejecutar

```bash
python main.py
```

---

##  Despliegue en producción

El sistema está diseñado para ejecutarse como tarea programada en Windows. Para generar el ejecutable:

```bash
pyinstaller --onefile main.py
```

El `.exe` resultante puede desplegarse en cualquier servidor Windows sin necesidad de instalar Python ni las dependencias.

---

##  Autor

**Mauricio Berbel Mercado**  
Técnico de Sistemas de Información — Positivo S+  
[LinkedIn](https://linkedin.com/in/tu-perfil) · [GitHub](https://github.com/berbelmercado)
