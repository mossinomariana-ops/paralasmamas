# =============================================================================
# auth.py — Acceso de las mamás: invitada (sin cuenta) o cuenta (mail + clave).
# =============================================================================
# - Invitada: crea una usuaria 'invitada' y deja la sesión iniciada de forma
#   PERSISTENTE en ese dispositivo (para que no pierda el acceso). Su base nace
#   vacía. Aviso claro: los datos viven solo en ese teléfono.
# - Cuenta: mail + clave (hash con werkzeug). Puede entrar desde cualquier lado.
#   Con "recordar en este dispositivo" la sesión queda guardada 90 días.
#
# La sesión guarda solo `uid` (id de la usuaria). require_login() protege todo:
# sin sesión válida → /bienvenida. Fija la usuaria activa en la capa de datos.
# =============================================================================

import re

from flask import (
    Blueprint, session, redirect, url_for, request, render_template
)
from werkzeug.security import generate_password_hash, check_password_hash

import database

auth_bp = Blueprint('auth', __name__)

# Rutas que NO requieren sesión iniciada (endpoints).
RUTAS_PUBLICAS = {
    'auth.bienvenida', 'auth.invitada', 'auth.registro', 'auth.login',
    'static', 'manifest', 'service_worker',
}

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def init_auth(app):
    app.register_blueprint(auth_bp)

    @app.before_request
    def require_login():
        if request.endpoint in RUTAS_PUBLICAS:
            return None
        uid = session.get('uid')
        if not uid or database.obtener_usuario(uid) is None:
            session.clear()
            return redirect(url_for('auth.bienvenida'))
        # Fija la usuaria activa para toda la capa de datos de este request.
        database.set_usuario_actual(uid)
        return None


def _iniciar_sesion(uid, recordar=True):
    session.clear()
    session['uid'] = uid
    session.permanent = bool(recordar)


# ── Pantalla de bienvenida: elegir cómo entrar ───────────────────────────────
@auth_bp.route('/bienvenida')
def bienvenida():
    if session.get('uid'):
        return redirect(url_for('inicio'))
    return render_template('bienvenida.html')


# ── Entrar sin cuenta (invitada) ─────────────────────────────────────────────
@auth_bp.route('/invitada', methods=['POST'])
def invitada():
    uid = database.crear_usuario('invitada')
    _iniciar_sesion(uid, recordar=True)   # persistente para no perder el acceso
    return redirect(url_for('inicio'))


# ── Crear cuenta ─────────────────────────────────────────────────────────────
@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if session.get('uid'):
        return redirect(url_for('inicio'))
    if request.method == 'GET':
        return render_template('login.html', modo='registro')

    email = (request.form.get('email') or '').strip().lower()
    clave = request.form.get('password') or ''
    clave2 = request.form.get('password2') or ''
    recordar = request.form.get('recordar') in ('1', 'on', 'true')

    error = None
    if not _EMAIL_RE.match(email):
        error = "Escribí un mail válido."
    elif len(clave) < 6:
        error = "La clave tiene que tener al menos 6 caracteres."
    elif clave != clave2:
        error = "Las dos claves no coinciden."
    elif database.obtener_usuario_por_email(email):
        error = "Ya existe una cuenta con ese mail. Probá iniciar sesión."
    if error:
        return render_template('login.html', modo='registro', error=error, email=email)

    uid = database.crear_usuario('cuenta', email=email,
                                 password_hash=generate_password_hash(clave))
    _iniciar_sesion(uid, recordar=recordar)
    return redirect(url_for('inicio'))


# ── Iniciar sesión (cuenta existente) ────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('uid'):
        return redirect(url_for('inicio'))
    if request.method == 'GET':
        return render_template('login.html', modo='login')

    email = (request.form.get('email') or '').strip().lower()
    clave = request.form.get('password') or ''
    recordar = request.form.get('recordar') in ('1', 'on', 'true')

    usuario = database.obtener_usuario_por_email(email)
    if usuario is None or not usuario.get('password_hash') \
            or not check_password_hash(usuario['password_hash'], clave):
        return render_template('login.html', modo='login',
                               error="Mail o clave incorrectos.", email=email)

    _iniciar_sesion(usuario['id'], recordar=recordar)
    return redirect(url_for('inicio'))


# ── Cerrar sesión ────────────────────────────────────────────────────────────
@auth_bp.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('auth.bienvenida'))
