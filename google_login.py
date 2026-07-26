# =============================================================================
# google_login.py — Verificar el "pase" que devuelve Entrar con Google.
# =============================================================================
# Cómo funciona el circuito, en criollo:
#   1. La pantalla de acceso muestra el botón oficial de Google (lo dibuja un
#      script de Google, no nosotros).
#   2. La mamá elige su cuenta. Google le devuelve al NAVEGADOR un pase firmado
#      (un "id_token": un texto largo con sus datos adentro y la firma de
#      Google).
#   3. El navegador nos manda ese pase a /auth/google.
#   4. Acá se comprueba que el pase sea auténtico ANTES de dejar entrar a nadie.
#      Sin este paso cualquiera podría inventarse un pase y entrar como otra.
#
# La comprobación se la pedimos al propio Google (oauth2.googleapis.com/tokeninfo):
# le mandamos el pase y nos contesta qué dice adentro, o error si está falseado
# o vencido. Se eligió así, y no con una biblioteca de criptografía, porque:
#   - no agrega NADA para instalar (urllib viene con Python), y en PythonAnywhere
#     gratis instalar cosas nuevas es un dolor de cabeza;
#   - oauth2.googleapis.com está en la lista de sitios permitidos de la cuenta
#     gratis, así que la llamada sale sin problema.
#
# Igual NO alcanza con que Google diga "el pase es válido": también hay que
# revisar que sea un pase PARA ESTA APP (el campo `aud` tiene que ser nuestro
# ID de cliente). Un pase válido de otra app no sirve para entrar acá.
# =============================================================================

import json
import time
import urllib.parse
import urllib.request

import config

TOKENINFO_URL = 'https://oauth2.googleapis.com/tokeninfo'

# Los dos textos que Google usa para decir "esto lo firmé yo".
EMISORES_VALIDOS = ('accounts.google.com', 'https://accounts.google.com')

# Si Google no contesta en este tiempo, se corta y se avisa. Sin esto, una
# demora de Google dejaría la pantalla colgada.
TIMEOUT_SEG = 10


class ErrorGoogle(Exception):
    """El pase no sirve. El mensaje es para mostrarle a la mamá."""


def verificar_id_token(id_token):
    """Devuelve los datos de la mamá si el pase es auténtico y es para esta app.
    Si no, levanta ErrorGoogle.

    Devuelve: {'sub', 'email', 'nombre', 'foto'}
    """
    if not config.GOOGLE_CLIENT_ID:
        raise ErrorGoogle("Entrar con Google no está configurado en esta app.")
    if not id_token or len(id_token) > 8000:
        raise ErrorGoogle("No llegó bien la respuesta de Google. Probá de nuevo.")

    datos = _consultar_a_google(id_token)

    # ── Controles de seguridad (el orden no importa, tienen que pasar todos) ──
    if datos.get('aud') != config.GOOGLE_CLIENT_ID:
        # Pase auténtico, pero emitido para OTRA aplicación.
        raise ErrorGoogle("Esa cuenta no se puede usar acá. Probá de nuevo.")
    if datos.get('iss') not in EMISORES_VALIDOS:
        raise ErrorGoogle("No pudimos verificar tu cuenta de Google.")
    try:
        if int(datos.get('exp', 0)) <= time.time():
            raise ErrorGoogle("La respuesta de Google venció. Probá de nuevo.")
    except (TypeError, ValueError):
        raise ErrorGoogle("No pudimos verificar tu cuenta de Google.")

    sub = (datos.get('sub') or '').strip()
    if not sub:
        raise ErrorGoogle("No pudimos verificar tu cuenta de Google.")

    # El mail se usa para reconocer a una mamá que ya tenía cuenta con mail y
    # clave. Solo vale si Google confirma que es de ella; si no, se ignora y la
    # cuenta queda identificada únicamente por `sub`.
    email = (datos.get('email') or '').strip().lower()
    verificado = str(datos.get('email_verified', '')).lower() in ('true', '1')
    if not verificado:
        email = ''

    return {
        'sub':    sub,
        'email':  email or None,
        'nombre': (datos.get('name') or '').strip()[:80] or None,
        'foto':   _foto_valida(datos.get('picture')),
    }


def _consultar_a_google(id_token):
    url = TOKENINFO_URL + '?' + urllib.parse.urlencode({'id_token': id_token})
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SEG) as resp:
            crudo = resp.read().decode('utf-8')
    except Exception:
        # Sin internet, Google caído, o pase falseado (contesta 400).
        raise ErrorGoogle("No pudimos verificar tu cuenta de Google. "
                          "Fijate que tengas internet y probá de nuevo.")
    try:
        datos = json.loads(crudo)
    except ValueError:
        raise ErrorGoogle("No pudimos verificar tu cuenta de Google.")
    if not isinstance(datos, dict) or datos.get('error') or datos.get('error_description'):
        raise ErrorGoogle("No pudimos verificar tu cuenta de Google.")
    return datos


def _foto_valida(url):
    """La foto se guarda para mostrarla en la barra de arriba. Solo se aceptan
    direcciones https de Google: así no queda forma de que entre por acá una
    imagen de cualquier otro lado."""
    url = (url or '').strip()
    if not url.startswith('https://'):
        return None
    host = urllib.parse.urlparse(url).hostname or ''
    if host == 'googleusercontent.com' or host.endswith('.googleusercontent.com'):
        return url[:400]
    return None
