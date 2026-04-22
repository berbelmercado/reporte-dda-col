# Reporte DDA Colombia — Automatización de Descarga y Persistencia

Sistema de automatización ETL que extrae el reporte de vehículos entregados por concesionarios a clientes finales (reporte DDA) desde un portal web, y persiste la información estructurada en una base de datos SQL Server para su uso en reportería y análisis operacional.

---

## ¿Qué hace este proyecto?

Este sistema automatiza de principio a fin el ciclo de obtención y procesamiento del **reporte DDA** (vehículos entregados por concesionarios a clientes finales).  
Lo que antes era un proceso manual y repetitivo, ahora se ejecuta de forma desatendida y confiable:

-  **Autenticación automática** en el portal de reportes corporativo mediante Selenium.  
-  **Descarga programada del reporte DDA**, evitando la intervención manual.  
-  **Transformación de datos con Pandas**, validando la calidad del archivo y filtrando únicamente la información relevante (entregas efectivas).  
-  **Persistencia en SQL Server**, con inserciones masivas optimizadas y lógica delta para garantizar que solo se almacenen VINs nuevos.  
-  **Empaquetado como ejecutable**, lo que permite desplegar el sistema en servidores Windows sin necesidad de instalar Python ni librerías adicionales.  
-  **Generación de logs centralizados**, facilitando el monitoreo y la trazabilidad de errores en todas las capas.  

En resumen, el proyecto convierte un flujo manual y propenso a errores en un **pipeline ETL robusto, automatizado y listo para producción**, asegurando que la información esté disponible de manera oportuna para análisis y reportería.

## Arquitectura

El proyecto aplica una arquitectura en capas con separación clara de responsabilidades. Cada capa tiene una única función y se comunica únicamente con las capas adyacentes.

```text
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
|   └── logger.py                # Registro de eventos:
|        # - Escribe logs INFO y ERROR en archivo log.txt
|        # - Formato: timestamp - nivel - mensaje
|        # - Usado por todas las capas del sistema
└── Log/
|   └── log.txt                                  # Almacenamiento de logs
|
└── Recursos                                     # Se guardan los archivos que descargamos.                     
    └── ecxel.xlsx
```
## Instalación y configuración

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


