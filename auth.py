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
import sqlite3

from flask import (
    Blueprint, session, redirect, url_for, request, render_template, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

import database
import google_login
import i18n

auth_bp = Blueprint('auth', __name__)

# Rutas que NO requieren sesión iniciada (endpoints).
RUTAS_PUBLICAS = {
    'auth.bienvenida', 'auth.invitada', 'auth.registro', 'auth.login',
    'auth.entrar_google',
    'static', 'manifest', 'service_worker',
}

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _pide_datos():
    """True si el pedido lo hace el JavaScript de la app (botones) y no el
    navegador cargando una pantalla."""
    return (request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.path.startswith('/api/'))


def init_auth(app):
    app.register_blueprint(auth_bp)

    @app.before_request
    def require_login():
        if request.endpoint in RUTAS_PUBLICAS:
            return None
        uid = session.get('uid')
        if not uid or database.obtener_usuario(uid) is None:
            session.clear()
            # A los botones de la app (JavaScript) NO se les puede contestar con
            # la pantalla de bienvenida: el navegador la sigue calladito y el JS
            # recibe una página donde esperaba datos. Resultado: la acción no se
            # hace y solo aparece un aviso raro de error. Se contesta un mensaje
            # claro y el JS recarga para que pueda volver a entrar.
            if _pide_datos():
                return jsonify({
                    'ok': False,
                    'sesion_cerrada': True,
                    'error': i18n.t("Se cerró tu sesión. Actualizá la página "
                                    "para volver a entrar."),
                }), 401
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
        error = i18n.t("Escribí un mail válido.")
    elif len(clave) < 6:
        error = i18n.t("La clave tiene que tener al menos 6 caracteres.")
    elif clave != clave2:
        error = i18n.t("Las dos claves no coinciden.")
    elif database.obtener_usuario_por_email(email):
        error = i18n.t("Ya existe una cuenta con ese mail. Probá iniciar sesión.")
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
                               error=i18n.t("Mail o clave incorrectos."), email=email)

    _iniciar_sesion(usuario['id'], recordar=recordar)
    return redirect(url_for('inicio'))


# ── Entrar con Google ────────────────────────────────────────────────────────
# La pantalla de acceso manda acá el pase firmado que devolvió Google. Se
# verifica (google_login.py) y recién ahí se decide a qué cuenta entra.
#
# POR QUÉ ES UN PEDIDO DE JAVASCRIPT Y NO UN FORMULARIO COMÚN: así el pedido
# sale desde NUESTRA propia página. Eso conserva la sesión que ya estaba
# abierta —clave para que una invitada se lleve sus datos— y evita tener que
# cargar direcciones de redirección en Google (alcanza con autorizar el dominio).
@auth_bp.route('/auth/google', methods=['POST'])
def entrar_google():
    # Solo se acepta desde nuestra página: una web ajena puede hacerle enviar un
    # formulario al navegador de la mamá, pero NO puede agregarle este encabezado.
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return jsonify({'ok': False, 'error': i18n.t("Pedido inválido.")}), 400

    datos = request.get_json(silent=True) or {}
    try:
        info = google_login.verificar_id_token(datos.get('credential'))
    except google_login.ErrorGoogle as e:
        return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400

    recordar = datos.get('recordar') is not False   # por defecto, sí
    try:
        uid, aviso = _resolver_cuenta_google(info, session.get('uid'))
    except sqlite3.IntegrityError:
        # Carrera rarísima (dos entradas a la vez con la misma cuenta): en vez de
        # romper con un error de base, se le pide que reintente.
        return jsonify({'ok': False,
                        'error': i18n.t("No pudimos entrar. Probá de nuevo.")}), 409

    _iniciar_sesion(uid, recordar=recordar)
    if aviso:
        session['aviso'] = aviso
    return jsonify({'ok': True})


def _resolver_cuenta_google(info, uid_sesion):
    """Decide a qué usuaria corresponde el pase de Google. Devuelve (uid, aviso).

    Las cuatro situaciones posibles, en orden:
      1. Esa cuenta de Google ya entró antes  → se entra a la suya de siempre.
      2. Hay una cuenta con ese mismo mail (la creó con mail y clave) → se le
         ata Google a esa cuenta, así no termina con dos cuentas separadas.
      3. Venía usando la app SIN cuenta       → su base se convierte en la
         cuenta: se lleva TODO lo que había cargado (decisión de producto).
      4. Nadie de lo anterior                 → cuenta nueva, base vacía.

    `aviso` es un mensaje para mostrarle arriba cuando pasó algo que conviene
    que sepa (que se llevó sus datos, o que NO se los llevó).
    """
    usuaria_sesion = database.obtener_usuario(uid_sesion) if uid_sesion else None
    era_invitada = bool(usuaria_sesion and usuaria_sesion.get('tipo') == 'invitada')
    tenia_cargado = era_invitada and database.tiene_datos(usuaria_sesion['id'])

    # Aviso para cuando entra a una cuenta que YA existía teniendo cosas
    # cargadas como invitada: esos datos NO se mezclan con los de la cuenta
    # (mezclarlos sería irreversible y podría duplicarle bolsitas).
    aviso_quedan = i18n.t(
        "Entraste a tu cuenta de Google. Lo que habías cargado sin cuenta quedó "
        "guardado aparte en este teléfono: para verlo, cerrá sesión y volvé a "
        "entrar sin cuenta."
    ) if tenia_cargado else None

    # 1. Cuenta de Google ya conocida.
    existente = database.obtener_usuario_por_google(info['sub'])
    if existente:
        database.actualizar_datos_google(existente['id'], info['nombre'], info['foto'])
        return existente['id'], aviso_quedan

    # 2. Ya tenía cuenta con ese mail (creada con mail y clave).
    por_mail = database.obtener_usuario_por_email(info['email']) if info['email'] else None
    if por_mail:
        database.vincular_google(por_mail['id'], info['sub'],
                                 email=info['email'],
                                 nombre=info['nombre'], foto=info['foto'])
        return por_mail['id'], aviso_quedan

    # 3. Venía como invitada: su base se convierte en la cuenta.
    if era_invitada:
        database.vincular_google(usuaria_sesion['id'], info['sub'],
                                 email=info['email'],
                                 nombre=info['nombre'], foto=info['foto'])
        return usuaria_sesion['id'], i18n.t(
            "¡Listo! Tu cuenta quedó creada y todo lo que habías cargado ya está "
            "guardado en ella. Ahora podés entrar desde cualquier teléfono."
        )

    # 4. Cuenta nueva, base vacía.
    uid = database.crear_usuario('cuenta', email=info['email'],
                                 google_sub=info['sub'],
                                 nombre=info['nombre'], foto=info['foto'])
    return uid, None


# ── Cerrar sesión ────────────────────────────────────────────────────────────
@auth_bp.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('auth.bienvenida'))
