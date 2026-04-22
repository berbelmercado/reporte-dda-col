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

reporte-dda-col/
├── main.py                      # Punto de entrada: carga .env y dispara el pipeline
├── controlador/
│   └── lectura_archivo_controlador.py  # Orquesta el pipeline completo:
│       # - Reintenta la descarga N veces (configurable vía .env)
│       # - Delega a ClienteSelenium y ProcesarArchivo
├── infraestructura/
│   └── cliente_selenium.py      # Automatización del navegador:
│       # - Login en portal SPOTFIRE (IPN + clave)
│       # - Navegación por 7 niveles de carpetas
│       # - Descarga del reporte DDA vía context-click
│       # - Manejo de SSL no seguro y cambio de ventana
│       # - Reintentos ante DOM inestable (StaleElementReference)
├── modelo/
│   ├── procesar_archivo.py      # Transformación ETL:
│   │   # - Valida que el archivo no esté vacío
│   │   # - Lee el Excel con Pandas
│   │   # - Filtra filas con Process == "Delivery"
│   │   # - Extrae columnas VIN y End_Date
│   │   # - Elimina el archivo tras procesarlo
│   └── inserta_datos.py         # Persistencia en SQL Server:
│       # - Conexión vía pyodbc (ODBC Driver 17)
│       # - Inserción masiva con fast_executemany
│       # - Lógica delta: inserta solo VINs nuevos
│       # - Limpia tabla temporal tras cada ejecución
├── servicios/
│   └── resolver_rutas.py        # Utilidad transversal:
│       # - Resuelve rutas relativas en desarrollo y en .exe (PyInstaller)
└── vista/
    └── logger.py                # Registro de eventos:
        # - Escribe logs INFO y ERROR en archivo .log
        # - Formato: timestamp - nivel - mensaje
        # - Usado por todas las capas del sistema

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
