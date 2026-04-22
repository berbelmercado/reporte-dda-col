import time
from os import getenv
import pygetwindow as gw

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

from webdriver_manager.chrome import ChromeDriverManager
from servicios.resolver_rutas import resource_path
from vista.logger import Logger
from modelo.procesar_archivo import ProcesarArchivo


_WAIT_IMPLICIT = 30
_WAIT_SHORT = 3
_WAIT_LOGIN = 10
_WAIT_REPORT = 20
_WAIT_DOWNLOAD = 15
_WAIT_EXPLICIT = 30


class ClienteSelenium:

    def __init__(self):
        self.ruta_driver = resource_path(getenv("RUTA_WEBDRIVER"))
        self.url_sopotfire = getenv("RUTA_SPOTFIRE")

        self.input_ipn = getenv("ID_INPUT_IPN")
        self.selec_clave = getenv("XPATH_INGRESAR_CLAVE")
        self.input_clave = getenv("ID_INPUT_CLAVE")
        self.siguiente = getenv("XPATH_SIGUIENTE")
        self.verificar = getenv("XPATH_VERIFICAR")

        self.carp_da3 = getenv("XPATH_CARPETA_DA3")
        self.carp_desing = getenv("XPATH_CARPETA_DESING")
        self.carp_col = getenv("XPATH_CARPETA_COL")
        self.carp_reports = getenv("XPATH_CARPETA_REPORTS")
        self.carp_reports_in_progress = getenv("XPATH_REPORTS_IN_PROGRES")
        self.carp_dda = getenv("XPATH_CARPETA_DDA")
        self.ds_report = getenv("XPATH_CARP_COL_DS_DDA_COLOMBIA")

        self.__ruta_descarga_reporte = resource_path(getenv("DESCARGA_REPORTE"))

        self.ipn = getenv("IPN")
        self.clave = getenv("CLAVE")
        self.validar_certificado = getenv("SSL_VERIFY")

        self.obj_log = Logger()
        self.obj_procesar_archivo = ProcesarArchivo()

    # ------------------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ------------------------------------------------------------------

    def descargar_archivo_dda(self) -> dict:
        driver = None
        try:
            driver = webdriver.Chrome(
                service=self._crear_servicio_driver(), options=self._crear_opciones()
            )
            driver.implicitly_wait(_WAIT_IMPLICIT)

            wait = WebDriverWait(driver, _WAIT_EXPLICIT)
            acciones = ActionChains(driver)

            driver.get(self.url_sopotfire)
            self._aceptar_sitio_no_seguro(driver)

            wait.until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "w-36.mb-4.tss-button.compact.ng-star-inserted")
                )
            ).click()

            time.sleep(_WAIT_LOGIN)
            self._validar_certificado_servidor()

            wait.until(
                EC.presence_of_element_located((By.ID, self.input_ipn))
            ).send_keys(self.ipn)
            wait.until(EC.element_to_be_clickable((By.XPATH, self.siguiente))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, self.selec_clave))).click()
            wait.until(
                EC.presence_of_element_located((By.ID, self.input_clave))
            ).send_keys(self.clave)
            wait.until(EC.element_to_be_clickable((By.XPATH, self.verificar))).click()

            self._navegar_carpetas(wait, acciones)
            self._cambiar_ventana(driver)

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)

            wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "/html/body/div/div[2]/div/div[1]/div/div/div[1]/div/div[1]/div/div/div[2]/div[1]/div[1]/div[2]",
                    )
                )
            ).click()

            self.context_click_safe(
                wait,
                acciones,
                (
                    By.XPATH,
                    "/html/body/div[1]/div[2]/div/div[1]/div/div/div[1]/div/div[2]"
                    "/div/div/div/div/div/div/div/div/div[1]/div[1]",
                ),
            )

            wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[2]/div[1]/div[1]/div")
                )
            ).click()
            wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[3]/div[1]/div[2]/div")
                )
            ).click()

            time.sleep(_WAIT_DOWNLOAD)
            driver.quit()
            return {"estado": True}

        except Exception as ex:
            if driver:
                driver.quit()
            self.obj_log.error(f"Error al iniciar el navegador: {ex}")
            return {"estado": False, "error": str(ex)}

    # ------------------------------------------------------------------
    # DOUBLE CLICK SEGURO
    # ------------------------------------------------------------------

    def double_click_safe(self, wait, acciones, locator, retries=3):
        for _ in range(retries):
            try:
                elemento = wait.until(EC.element_to_be_clickable(locator))
                acciones.move_to_element(elemento).double_click().perform()
                return
            except StaleElementReferenceException:
                time.sleep(1)
        raise StaleElementReferenceException("double_click falló por DOM inestable")

    # ------------------------------------------------------------------
    # CONTEXT CLICK SEGURO
    # ------------------------------------------------------------------

    def context_click_safe(self, wait, acciones, locator, retries=3):
        for _ in range(retries):
            try:
                elemento = wait.until(EC.element_to_be_clickable(locator))
                acciones.move_to_element(elemento).context_click().perform()
                return
            except StaleElementReferenceException:
                time.sleep(1)
        raise StaleElementReferenceException("context_click falló por DOM inestable")

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _navegar_carpetas(self, wait, acciones):
        rutas = [
            self.carp_da3,
            self.carp_desing,
            self.carp_col,
            self.carp_reports,
            self.carp_reports_in_progress,
            self.carp_dda,
            self.ds_report,
        ]
        for ruta in rutas:
            self.double_click_safe(wait, acciones, (By.XPATH, ruta))

    def _cambiar_ventana(self, driver):
        original = driver.current_window_handle
        WebDriverWait(driver, _WAIT_EXPLICIT).until(lambda d: len(d.window_handles) > 1)
        for h in driver.window_handles:
            if h != original:
                driver.switch_to.window(h)
                break

    def _crear_servicio_driver(self):
        try:
            return Service(ChromeDriverManager().install())
        except Exception:
            return Service(executable_path=self.ruta_driver)

    def _crear_opciones(self):
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": self.__ruta_descarga_reporte,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )
        return options

    def _aceptar_sitio_no_seguro(self, driver):
        if self.validar_exitencia(driver, "details-button", "ID"):
            WebDriverWait(driver, _WAIT_EXPLICIT).until(
                EC.element_to_be_clickable((By.ID, "details-button"))
            ).click()
            WebDriverWait(driver, _WAIT_EXPLICIT).until(
                EC.element_to_be_clickable((By.ID, "proceed-link"))
            ).click()

    def _validar_certificado_servidor(self):
        if self.validar_certificado != "True":
            return
        ventanas = [w for w in gw.getWindowsWithTitle("Chrome") if not w.isActive]
        if ventanas:
            ventanas[0].activate()

    def validar_exitencia(self, nav_driver, identificador, tipo_id):
        try:
            by = getattr(By, tipo_id)
            WebDriverWait(nav_driver, _WAIT_SHORT).until(
                EC.presence_of_element_located((by, identificador))
            )
            return True
        except Exception:
            return False
