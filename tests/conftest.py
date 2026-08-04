# =============================================================================
# conftest.py — La preparación que corre ANTES de cualquier prueba.
# =============================================================================
# LO MÁS IMPORTANTE DE ESTE ARCHIVO: las pruebas NO tocan los datos reales.
#
# La app, apenas se importa, escribe en disco: `database.py` crea la carpeta
# data/, `app.py` crea la base central de cuentas y guarda la clave de sesiones
# en data/secret.key. Si dejáramos que eso pasara normalmente, correr las
# pruebas ensuciaría (o rompería) la información de las mamás que ya usan la app.
#
# Por eso acá, ANTES de importar `app`, se le cambia a `database` la carpeta de
# datos por una temporal del sistema. Como `app.py` arma la ruta del secret.key
# a partir de `database.DATA_DIR`, todo cae en la carpeta temporal. Al terminar,
# la carpeta se borra sola.
#
# El orden de las líneas de abajo NO es decorativo: si se importara `app` antes
# de reescribir las rutas, ya sería tarde.
# =============================================================================

import atexit
import json
import os
import shutil
import sys
import tempfile
from datetime import date, timedelta

import pytest

# La carpeta del proyecto (la de arriba de tests/) tiene que estar en el camino
# de búsqueda de Python para poder importar app, logica, database, etc.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import database  # noqa: E402  (tiene que importarse antes de desviarlo)

DATOS_REALES = database.DATA_DIR

# ── El desvío a una carpeta temporal ─────────────────────────────────────────
_TMP = tempfile.mkdtemp(prefix='lactancia-tests-')
database.DATA_DIR = _TMP
database.USUARIOS_DB = os.path.join(_TMP, 'usuarios.db')


@atexit.register
def _limpiar():
    shutil.rmtree(_TMP, ignore_errors=True)


import app as app_modulo  # noqa: E402  (recién ahora, con las rutas desviadas)
import config             # noqa: E402
import logica             # noqa: E402

# Red de seguridad: si alguna vez alguien cambia el orden de arriba y las
# pruebas vuelven a apuntar a los datos reales, esto lo corta en seco.
assert database.DATA_DIR == _TMP, "Las pruebas apuntan a los datos REALES"
assert database.DATA_DIR != DATOS_REALES, "Las pruebas apuntan a los datos REALES"

# ── La cookie de sesión, solo para las pruebas ───────────────────────────────
# En el servidor la cookie está marcada como segura: el navegador la guarda solo
# si la conexión es https. El cliente de pruebas de Flask habla http, así que con
# la marca puesta NINGUNA prueba podría iniciar sesión y todas fallarían por el
# motivo equivocado. Se apaga acá y solo acá.
#
# Antes de apagarla se guarda cómo venía de app.py: eso es lo que va a regir en
# PythonAnywhere, y es lo que comprueba la prueba de test_seguridad.py. Sin esta
# copia, la prueba leería el valor apagado de acá y no verificaría nada.
COOKIE_SEGURA_EN_EL_SERVIDOR = app_modulo.app.config['SESSION_COOKIE_SECURE']

app_modulo.app.config['SESSION_COOKIE_SECURE'] = False


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope='session')
def flask_app():
    app_modulo.app.config['TESTING'] = True
    return app_modulo.app


@pytest.fixture(autouse=True)
def contexto(flask_app):
    """Contexto de pedido activo en TODAS las pruebas.

    Los mensajes de error de la app pasan por i18n.t(), que necesita saber el
    idioma del pedido en curso. Sin esto, una prueba de validación fallaría con
    un error críptico de Flask en vez de comprobar lo que quiere comprobar."""
    with flask_app.test_request_context():
        yield


@pytest.fixture
def cliente(flask_app):
    """Una usuaria invitada nueva, ya con la sesión abierta.

    Cada prueba se lleva SU usuaria y SU base vacía (data/u_<id>.db en la
    carpeta temporal), así ninguna prueba puede ensuciar a otra."""
    c = flask_app.test_client()
    resp = c.post('/invitada')
    assert resp.status_code == 302
    return c


@pytest.fixture
def cliente_2(flask_app):
    """Una SEGUNDA usuaria invitada, para las pruebas de aislamiento."""
    c = flask_app.test_client()
    c.post('/invitada')
    return c


@pytest.fixture
def assetlinks_falso():
    """El archivo que en el servidor pega Google Play, pero de mentira.

    Se escribe en la carpeta TEMPORAL (database.DATA_DIR ya viene desviado ahí
    arriba) y se borra al terminar, así la prueba del archivo ausente no depende
    del orden en que corran las pruebas."""
    ruta = os.path.join(database.DATA_DIR, 'assetlinks.json')
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump([{
            'relation': ['delegate_permission/common.handle_all_urls'],
            'target': {
                'namespace': 'android_app',
                'package_name': 'com.paralasmamas.lactancia',
                'sha256_cert_fingerprints': ['AA:BB:CC'],
            },
        }], f)
    yield ruta
    os.remove(ruta)


@pytest.fixture
def usuaria():
    """Una usuaria activa para probar la capa de datos sin pasar por las rutas.

    Hace falta porque database exige saber de quién es la base antes de abrirla
    (si no, levanta "No hay usuaria activa en este request")."""
    uid = database.crear_usuario('invitada')
    database.set_usuario_actual(uid)
    yield uid
    database._local.uid = None


# ── Ayudantes ────────────────────────────────────────────────────────────────
AJAX = {'X-Requested-With': 'XMLHttpRequest'}


def uid_de(cliente):
    """El id de usuaria que tiene guardado en la sesión ese cliente."""
    with cliente.session_transaction() as s:
        return s.get('uid')


def post(cliente, url, **campos):
    """POST como lo hace el JavaScript de la app (con la cabecera que la app usa
    para saber que tiene que contestar datos y no una pantalla)."""
    return cliente.post(url, data=campos, headers=AJAX)


def payload(cliente):
    """El estado completo de la app tal como lo recibe el navegador."""
    r = cliente.get('/api/lactancia', headers=AJAX)
    assert r.status_code == 200
    return r.get_json()


def crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=0,
          hora='00:00', notas=''):
    """Carga una bolsita y devuelve la respuesta.

    `dias_atras` permite fabricar leche vieja (para probar vencimientos) sin
    depender de la hora a la que se corran las pruebas. La hora por defecto es
    medianoche justamente por eso: una extracción de HOY a las 08:00 sería
    futura —y la app la rechazaría— si las pruebas se corrieran a las 7 de la
    mañana."""
    fecha = (date.today() - timedelta(days=dias_atras)).isoformat()
    return post(cliente, '/api/lactancia/crear', ubicacion=ubicacion,
                volumen_ml=volumen_ml, fecha_extraccion=fecha,
                hora_extraccion=hora, notas=notas)


def crear_id(cliente, **kw):
    """Carga una bolsita y devuelve su id (la última de su lista)."""
    datos = crear(cliente, **kw).get_json()
    assert datos['ok'], datos
    lista = datos[kw.get('ubicacion', 'freezer')]
    return max(p['id'] for p in lista)


def params_base(**cambios):
    """Los parámetros por defecto de la app, con los cambios que se le pidan.

    Se arman desde config.DEFAULTS (no a mano) para que si mañana cambia un
    valor por defecto, las pruebas sigan midiendo lo que corresponde."""
    p = logica._lac_params(perfil={})
    p.update(cambios)
    return p
