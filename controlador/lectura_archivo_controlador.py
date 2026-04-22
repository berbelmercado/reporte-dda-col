from infraestructura.cliente_selenium import ClienteSelenium
from modelo.procesar_archivo import ProcesarArchivo
from vista.logger import Logger
from os import getenv


class etl_dda_controlador:
    def __init__(self):

        self.obj_cliente_selenium = ClienteSelenium()
        self.obj_procesar_archivo = ProcesarArchivo()
        self.intentos_descarga = getenv("INTENTOS_DESCARGA")
        self.obj_log = Logger()
        self.resultado_descarga = {}

    def descarga_proceso_reporte_dda(self):

        contador = 0
        while contador < int(self.intentos_descarga):

            self.resultado_descarga = self.obj_cliente_selenium.descargar_archivo_dda()
            if self.resultado_descarga["estado"]:
                self.obj_log.log("Archivo descargado exitosamente.")
                return True
                break
            else:
                self.obj_log.error(
                    f"{self.resultado_descarga['error']} Intento {contador + 1} de {self.intentos_descarga}."
                )
                contador += 1
                continue
        return False

    def procesar_reporte_dda(self):
        if self.descarga_proceso_reporte_dda():
            self.obj_procesar_archivo.leer_modificar_archivo()
        else:
            self.obj_log.error(
                "No se pudo descargar el archivo después de varios intentos."
            )
