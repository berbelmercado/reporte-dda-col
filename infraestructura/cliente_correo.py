"""
Módulo para enviar alertas por correo cuando una ejecución falla.

Usa un relay SMTP interno: sin usuario, sin contraseña y sin cifrado.
"""

import smtplib
import socket
from datetime import datetime
from email.message import EmailMessage
from os import getenv

from vista.logger import Logger

_TIMEOUT_SMTP = 30


class ClienteCorreo:

    def __init__(self):
        self.remitente = getenv("CORREO_REMITENTE")
        self.servidor = getenv("SERVIDOR_SMTP")
        self.puerto = getenv("PUERTO_SERVIDOR_SMTP")
        # Varios destinatarios separados por coma
        self.destinatarios = [
            correo.strip()
            for correo in (getenv("DESTINATARIO") or "").split(",")
            if correo.strip()
        ]
        self.obj_log = Logger()

    def enviar_alerta_fallo(self, log_ejecucion: str) -> bool:
        """
        Envía un correo avisando que la ejecución falló, con el log de la corrida adjunto.

        Parámetros:
        -----------
        log_ejecucion : str
            Líneas del log de la ejecución que falló.

        Returns:
        --------
        bool
            True si el correo se envió, False en caso contrario.
        """
        if not self.destinatarios:
            self.obj_log.error("No se envía la alerta: DESTINATARIO está vacío en el .env")
            return False

        try:
            fecha = datetime.now()
            equipo = socket.gethostname()

            mensaje = EmailMessage()
            mensaje["Subject"] = (
                f"[Reporte DDA] Falló la ejecución del {fecha:%Y-%m-%d %H:%M} en {equipo}"
            )
            mensaje["From"] = self.remitente
            mensaje["To"] = ", ".join(self.destinatarios)
            mensaje.set_content(
                f"La ejecución del reporte DDA en {equipo} terminó con errores "
                f"el {fecha:%Y-%m-%d} a las {fecha:%H:%M}.\n\n"
                "Se adjunta el log de esa ejecución.\n"
            )
            mensaje.add_attachment(
                log_ejecucion.encode("utf-8"),
                maintype="text",
                subtype="plain",
                filename=f"log_dda_{fecha:%Y%m%d_%H%M%S}.txt",
            )

            with smtplib.SMTP(self.servidor, int(self.puerto), timeout=_TIMEOUT_SMTP) as smtp:
                smtp.send_message(mensaje)

            self.obj_log.log(
                f"Alerta de fallo enviada a: {', '.join(self.destinatarios)}"
            )
            return True
        except Exception as ex:
            self.obj_log.error(f"No se pudo enviar la alerta por correo: {ex}")
            return False
