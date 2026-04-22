from dotenv import load_dotenv
from servicios.resolver_rutas import resource_path
from controlador.lectura_archivo_controlador import etl_dda_controlador

if __name__ == "__main__":

    load_dotenv(resource_path(".env"))

    obj_controlador = etl_dda_controlador()
    obj_controlador.procesar_reporte_dda()
