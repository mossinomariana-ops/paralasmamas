# =============================================================================
# correo.py — Envío de mail de la app Lactancia (hoy: las sugerencias).
# =============================================================================
# Se manda por el SMTP de Gmail A PROPÓSITO: en las cuentas GRATIS de
# PythonAnywhere las conexiones de salida están bloqueadas, con una excepción
# justamente para los servidores de correo de Google. Cualquier otro proveedor
# (Outlook, Zoho, un SMTP propio) NO va a funcionar sin pagar la cuenta.
#
# SON DOS CASILLAS DISTINTAS (pedido de Mari): `usuario` es una casilla NUEVA
# hecha solo para la app, la única que envía y la única que lleva contraseña;
# `destino` es la casilla personal de Mari, que solo recibe y nunca se toca.
#
# La clave NO es la contraseña de Gmail: es una "contraseña de aplicación" que
# genera Google (hace falta tener la verificación en dos pasos activada). Sirve
# solo para enviar mails y no da acceso a la cuenta. Los pasos están en
# DEPLOY.md.
#
# Dónde se configuran los datos (en este orden):
#   1. Variables de entorno CORREO_USUARIO / CORREO_CLAVE / CORREO_DESTINO
#   2. El archivo data/correo.json (esa carpeta es privada y NO va al repo):
#        {"usuario": "casilla-de-la-app@gmail.com",
#         "clave": "abcd efgh ijkl mnop",
#         "destino": "casilla-personal@gmail.com"}
#
# Mientras no esté configurado, `activo()` da False y la app esconde la tarjeta
# de Sugerencias: nadie escribe algo que no se iba a poder mandar.
# =============================================================================

import json
import os
import smtplib
import ssl
from email.message import EmailMessage

import database

_CONFIG_FILE = os.path.join(database.DATA_DIR, 'correo.json')

SERVIDOR = 'smtp.gmail.com'
PUERTO = 465          # SSL directo (el más simple y el que menos se traba)
TIMEOUT = 20          # segundos: si Gmail no responde, cortamos y avisamos


def _de_archivo():
    """Lee data/correo.json. Si no existe o está mal escrito, devuelve {}."""
    try:
        with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def config():
    """Datos de la casilla que envía y de la que recibe. Las variables de
    entorno le ganan al archivo (útil para probar sin tocar nada)."""
    archivo = _de_archivo()
    usuario = (os.environ.get('CORREO_USUARIO') or archivo.get('usuario') or '').strip()
    clave = (os.environ.get('CORREO_CLAVE') or archivo.get('clave') or '').strip()
    destino = (os.environ.get('CORREO_DESTINO') or archivo.get('destino') or usuario).strip()
    return {'usuario': usuario, 'clave': clave, 'destino': destino}


def activo():
    """True si hay casilla configurada (o sea: se pueden mandar sugerencias)."""
    c = config()
    return bool(c['usuario'] and c['clave'] and c['destino'])


def enviar(asunto, cuerpo, responder_a=None):
    """Manda un mail de texto. Devuelve True si Gmail lo aceptó.

    Lanza RuntimeError con un mensaje entendible si no está configurado, si
    Google rechaza la clave o si no se pudo llegar al servidor. El que llama
    decide qué mostrarle a la usuaria."""
    c = config()
    if not (c['usuario'] and c['clave'] and c['destino']):
        raise RuntimeError("El envío de correo todavía no está configurado.")

    msg = EmailMessage()
    msg['Subject'] = asunto
    msg['From'] = c['usuario']
    msg['To'] = c['destino']
    # Así, al responder el mail, la respuesta le llega a quien dejó su correo
    # (si no dejó ninguno, responder va a la casilla de la app).
    if responder_a:
        msg['Reply-To'] = responder_a
    msg.set_content(cuerpo)

    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP_SSL(SERVIDOR, PUERTO, context=contexto, timeout=TIMEOUT) as smtp:
            smtp.login(c['usuario'], c['clave'])
            smtp.send_message(msg)
        return True
    except smtplib.SMTPAuthenticationError:
        raise RuntimeError("Google rechazó la clave de la casilla de la app.")
    except (smtplib.SMTPException, OSError):
        # Incluye timeouts y cortes de red. Google cambia sus direcciones cada
        # tanto, así que un fallo suelto acá no significa que esté mal armado.
        raise RuntimeError("No pudimos conectarnos al servidor de correo.")
