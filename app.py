# =============================================================================
# app.py — App Lactancia (banco de leche materna) · Flask · multiusuario.
# =============================================================================
# App independiente para que cada mamá lleve su stock de leche. Extraída del
# módulo Lactancia del fondo familiar, sin nada de gastos/calendario/rutina.
# Cada usuaria (invitada o con cuenta) tiene su propia base y arranca vacía.
# =============================================================================

import os
import json
import re
import secrets
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for, jsonify,
    session, send_from_directory, Response
)

import auth
import config
import correo
import database
import i18n
import logica
from auth import init_auth

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Validación mínima del correo de contacto (opcional) de las sugerencias: solo
# chequea la forma "algo@algo.algo". El que manda de verdad es Gmail.
_EMAIL_SIMPLE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ── Base central de cuentas ──────────────────────────────────────────────────
database.init_usuarios()

# ── Secret key persistente (para que las sesiones sobrevivan reinicios) ───────
_SECRET_FILE = os.path.join(database.DATA_DIR, 'secret.key')
if os.path.exists(_SECRET_FILE):
    with open(_SECRET_FILE, 'r', encoding='utf-8') as f:
        app.secret_key = f.read().strip()
else:
    app.secret_key = secrets.token_hex(32)
    with open(_SECRET_FILE, 'w', encoding='utf-8') as f:
        f.write(app.secret_key)

app.config['SESSION_COOKIE_NAME'] = 'lactancia_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=90)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# La cookie de sesión SOLO viaja por conexión segura (https). Sin esto, si una
# mamá abre la app por http —un enlace viejo, un QR mal hecho— su sesión viajaría
# a la vista de cualquiera que comparta la red.
#
# Queda ENCENDIDO por defecto, que es como corre en PythonAnywhere (entra por
# WSGI, no por el bloque de abajo). Se apaga en los dos únicos lugares donde no
# hay https y encenderlo dejaría todo sin sesión: el arranque local del final de
# este archivo y tests/conftest.py.
app.config['SESSION_COOKIE_SECURE'] = True

init_auth(app)


def _es_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _horas_texto(horas):
    """Horas (float) → texto corto para un mensaje: '40 min', '2 h', '2 h 20 min'."""
    minutos = max(1, int(round(horas * 60)))
    h, m = divmod(minutos, 60)
    if not h:
        return f"{m} min"
    return f"{h} h" if not m else f"{h} h {m} min"


def _static_version():
    """mtime más reciente de los estáticos principales → cache-busting."""
    try:
        paths = [os.path.join(app.static_folder, n)
                 for n in ('style.css', 'lactancia.js', 'pwa.js', 'google.js')]
        return str(int(max(os.path.getmtime(p) for p in paths if os.path.exists(p))))
    except Exception:
        return '0'


@app.context_processor
def inject_config():
    uid = session.get('uid')
    usuario = database.obtener_usuario(uid) if uid else None
    return {
        'cfg': {
            'app_name': config.APP_NOMBRE,
            'paleta_light': config.PALETA_LIGHT,
            'paleta_dark': config.PALETA_DARK,
            'marca': config.MARCA,
            # Vacío = no hay Entrar con Google configurado y el botón no se dibuja.
            'google_client_id': config.GOOGLE_CLIENT_ID,
            # False = todavía no hay casilla de correo configurada, así que la
            # tarjeta de Sugerencias no se dibuja (nadie escribe al vacío).
            'sugerencias': correo.activo(),
        },
        # Largo mínimo de la clave al crear cuenta. Sale de auth.py para que la
        # pantalla y el servidor no puedan decir cosas distintas.
        'clave_minima': auth.CLAVE_MINIMA,
        # Mensaje de una sola vez (ej: "tus datos quedaron en la cuenta"). Se
        # saca de la sesión al mostrarlo, así no vuelve a aparecer al recargar.
        'aviso': session.pop('aviso', None),
        # Traducción: `t` para los textos de las plantillas, `idioma` para saber
        # qué ofrece la tarjeta del header, y el diccionario que se le pasa al
        # JavaScript para los textos que arma él.
        't': i18n.t,
        'idioma': i18n.idioma_actual(),
        'dic_idioma': i18n.diccionario_js(),
        'static_version': _static_version(),
        'usuario': usuario,
        'es_invitada': bool(usuario and usuario.get('tipo') == 'invitada'),
    }


# =============================================================================
# PÁGINA PRINCIPAL — el banco de leche
# =============================================================================
@app.route('/')
def inicio():
    return render_template('lactancia.html', datos=logica._lac_payload())


# =============================================================================
# PANTALLA DE PRIVACIDAD
# =============================================================================
# Se lee SIN cuenta a propósito (está en RUTAS_PUBLICAS, en auth.py). Dos motivos:
#   - Una mamá tiene derecho a saber qué se va a guardar ANTES de entrar, no
#     después.
#   - Google pide una dirección pública de política de privacidad para sacar el
#     "Entrar con Google" del modo de prueba. Si esta pantalla mandara a la de
#     bienvenida, Google no la podría leer y el trámite no avanza.
@app.route('/privacidad')
def privacidad():
    # Se muestra la casilla DE LA APP (`usuario`), nunca la personal de la
    # responsable (`destino`): esta pantalla la puede leer cualquiera, incluidos
    # los robots que juntan direcciones para spam. Si todavía no hay correo
    # configurado no se muestra ninguna, y el texto ofrece el formulario de
    # Sugerencias de adentro de la app.
    return render_template('privacidad.html', contacto=correo.config()['usuario'])


@app.route('/api/lactancia')
def api_lactancia():
    return jsonify({'ok': True, **logica._lac_payload()})


@app.route('/api/lactancia/crear', methods=['POST'])
def api_lactancia_crear():
    try:
        datos = logica._lac_leer_form_alta(request.form, logica._lac_params())
        database.agregar_partida_lactancia(**datos)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/<int:id>/cerrar', methods=['POST'])
def api_lactancia_cerrar(id):
    try:
        partida = database.obtener_partida_lactancia(id)
        if partida is None:
            raise ValueError(f"No existe la bolsita {id}.")
        if partida['motivo_cierre']:
            raise ValueError("La bolsita ya está cerrada.")

        motivo = request.form.get('motivo', '')
        if motivo not in ('usada', 'descartada'):
            raise ValueError(f"Motivo de cierre inválido: {motivo}")

        fecha_cierre = logica._lac_parsear_fecha_cierre(request.form.get('fecha_cierre'))
        notas = (request.form.get('notas') or '').strip()[:200] or None

        consumido_ml = None
        if motivo == 'usada':
            crudo = (request.form.get('consumido_ml') or '').strip()
            if crudo:
                try:
                    consumido_ml = int(crudo)
                except ValueError:
                    raise ValueError("El consumo (ml) debe ser un número entero.")
                if not 0 <= consumido_ml <= partida['volumen_ml']:
                    raise ValueError(
                        f"El consumo debe estar entre 0 y {partida['volumen_ml']} ml "
                        "(lo que tenía la bolsita).")

        database.cerrar_partida_lactancia(id, motivo, fecha_cierre, notas, consumido_ml)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/freezar', methods=['POST'])
def api_lactancia_freezar():
    from datetime import date
    try:
        params = logica._lac_params()
        ahora = datetime.now()
        crudo = (request.form.get('ids') or '').strip()
        try:
            ids = [int(x) for x in crudo.split(',') if x.strip()]
        except ValueError:
            raise ValueError(f"Ids inválidos: {crudo}")
        if not ids:
            raise ValueError("Tildá al menos una bolsita de heladera para freezar.")

        confirmar_vencidas = request.form.get('confirmar_vencidas') == '1'
        partidas = []
        vencidas = 0
        for pid in ids:
            row = database.obtener_partida_lactancia(pid)
            if row is None:
                raise ValueError(f"No existe la bolsita {pid}.")
            p = dict(row)
            if p['ubicacion'] != 'heladera':
                raise ValueError("Solo se freezan bolsitas de heladera.")
            if p['motivo_cierre']:
                raise ValueError("Una de las bolsitas tildadas ya está cerrada.")
            if not logica._lac_freezable(p, params, ahora):
                vencidas += 1
            partidas.append(p)

        if vencidas and not confirmar_vencidas:
            raise ValueError(
                "Hay bolsitas vencidas entre las tildadas: confirmá que se pasaron "
                "al freezer antes de vencerse para poder freezarlas.")

        # Para juntar DOS o más extracciones en una sola bolsa, todas tienen que
        # estar ya frías: se pide un mínimo de horas en la heladera desde la
        # extracción (configurable). Con una sola partida no se combina nada, así
        # que la regla no aplica.
        minimo = params['combinar_min_horas']
        if len(partidas) > 1 and minimo > 0:
            tibias = [p for p in partidas
                      if logica._lac_horas_en_heladera(p, ahora) < minimo]
            if tibias:
                falta = max(minimo - logica._lac_horas_en_heladera(p, ahora)
                            for p in tibias)
                cuantas = (i18n.t('Una de las bolsitas tildadas') if len(tibias) == 1
                           else i18n.t('{n} de las bolsitas tildadas', n=len(tibias)))
                raise ValueError(i18n.t(
                    "{cuantas} todavía no llegó a las {minimo} h en la heladera. "
                    "Para combinarlas las dos tienen que estar a la misma "
                    "temperatura: esperá {falta} y volvé a probar.",
                    cuantas=cuantas, minimo=minimo, falta=_horas_texto(falta)))

        volumen_ml = sum(p['volumen_ml'] for p in partidas)
        if volumen_ml > 2000:
            raise ValueError("El volumen combinado supera los 2000 ml; freezá en tandas.")
        if params['bolsa_capacidad_activa'] and volumen_ml > params['bolsa_capacidad_ml']:
            raise ValueError(i18n.t(
                "Lo tildado suma {suma} ml y tus bolsitas son de {tope} ml. "
                "Tildá menos bolsitas, o subí la capacidad en Ajustes.",
                suma=volumen_ml, tope=params['bolsa_capacidad_ml']))

        mas_vieja = min(partidas,
                        key=lambda p: (p['fecha_extraccion'], p['hora_extraccion'] or ''))
        database.combinar_partidas_lactancia(
            ids, mas_vieja['fecha_extraccion'], mas_vieja['hora_extraccion'],
            volumen_ml, date.today().isoformat())
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/<int:id>/bajar', methods=['POST'])
def api_lactancia_bajar(id):
    from datetime import date
    try:
        database.bajar_partida_lactancia(id, date.today().isoformat())
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/recordatorio', methods=['POST'])
def api_lactancia_recordatorio():
    try:
        activo = request.form.get('activo') in ('1', 'true', 'on', 'True')
        hora = (request.form.get('hora') or '').strip()
        try:
            datetime.strptime(hora, '%H:%M')
        except ValueError:
            raise ValueError("La hora del recordatorio debe ser HH:MM (ej: 21:00).")
        database.guardar_perfil(recordatorio_activo=1 if activo else 0,
                                recordatorio_hora=hora)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/config', methods=['POST'])
def api_lactancia_config():
    """Guarda las Configuraciones de la mamá (tiempos, capacidad de bolsitas y
    confirmaciones). Solo se tocan los campos que vengan en el formulario."""
    try:
        campos = {}

        for corto, _clave in logica.LAC_PARAMS_NUM:
            if corto not in request.form:
                continue
            crudo = (request.form.get(corto) or '').strip()
            try:
                valor = int(crudo)
            except ValueError:
                raise ValueError(f"«{corto.replace('_', ' ')}» tiene que ser un número entero.")
            minimo, maximo = config.LIMITES[corto]
            if not minimo <= valor <= maximo:
                raise ValueError(
                    f"«{corto.replace('_', ' ')}» tiene que estar entre {minimo} y {maximo}.")
            campos[corto] = valor

        for corto in ('bolsa_capacidad_activa', 'pedir_confirmacion'):
            if corto in request.form:
                campos[corto] = 1 if request.form.get(corto) in ('1', 'true', 'on', 'True') else 0

        if not campos:
            raise ValueError("No llegó ninguna configuración para guardar.")

        # Coherencia: avisar antes de vencer, no después.
        nuevos = {**logica._lac_params(), **campos}
        if nuevos['aviso_heladera_horas'] > nuevos['heladera_horas']:
            raise ValueError("El aviso de la heladera no puede ser mayor que el "
                             "tiempo de vencimiento en la heladera.")
        if nuevos['aviso_descongelada_horas'] > nuevos['descongelada_horas']:
            raise ValueError("El aviso de la leche descongelada no puede ser mayor "
                             "que su tiempo de vencimiento.")
        if nuevos['aviso_freezer_dias'] > nuevos['freezer_meses'] * 30:
            raise ValueError("El aviso del freezer no puede ser mayor que el tiempo "
                             "de vencimiento en el freezer.")

        database.guardar_perfil(**campos)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/sugerencia', methods=['POST'])
def api_lactancia_sugerencia():
    """Sugerencia de una mamá → mail a la casilla de la app.

    Es ANÓNIMA: no se guarda nada ni se manda quién la escribió. Lo único
    opcional es el correo de contacto que ella misma tipee, que viaja como
    "responder a". Se adjunta el idioma y si entró como invitada o con cuenta,
    que no identifican a nadie pero ayudan a entender la sugerencia.

    Como NO se guarda copia (decisión de Mari), si el envío falla hay que
    avisarle en pantalla para que no se pierda lo que escribió."""
    try:
        if not correo.activo():
            raise ValueError("Las sugerencias todavía no están disponibles.")

        texto = (request.form.get('texto') or '').strip()[:1000]
        if not texto:
            raise ValueError("Escribí tu sugerencia antes de enviarla.")

        contacto = (request.form.get('email') or '').strip()[:120]
        if contacto and not _EMAIL_SIMPLE.match(contacto):
            raise ValueError("Ese correo no parece válido. Revisalo o dejalo vacío.")

        # Freno simple contra el doble toque y el spam de una misma sesión.
        ahora = datetime.now()
        ultimo = session.get('sug_ultimo')
        if ultimo:
            try:
                pasados = (ahora - datetime.fromisoformat(ultimo)).total_seconds()
            except (TypeError, ValueError):
                pasados = None   # valor viejo o roto: no frena a nadie
            if pasados is not None and pasados < 60:
                raise ValueError("Esperá un minuto antes de enviar otra sugerencia.")

        uid = session.get('uid')
        usuario = database.obtener_usuario(uid) if uid else None
        tipo = (usuario or {}).get('tipo') or 'desconocida'
        cuerpo = (
            f"{texto}\n\n"
            f"---\n"
            f"Enviada desde la app Lactancia el {ahora.strftime('%d/%m/%Y %H:%M')}\n"
            f"Idioma: {i18n.idioma_actual()} · Entró como: {tipo}\n"
            f"Correo de contacto: {contacto or '(no dejó)'}\n"
        )
        correo.enviar('Sugerencia — app Lactancia', cuerpo, responder_a=contacto or None)
        # Recién acá se marca la marca de tiempo: si el envío falló, la mamá
        # puede reintentar en el momento sin esperar el minuto.
        session['sug_ultimo'] = ahora.isoformat()

        if _es_ajax():
            return jsonify({'ok': True})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except RuntimeError as e:
        # El correo no salió. Se avisa con el texto de correo.py, que ya está
        # escrito para que se entienda sin saber de tecnología.
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 502
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


def _volver_a():
    """A qué pantalla volver después de una acción hecha con un formulario común.

    Es la pantalla desde la que se apretó el botón, o la principal si no se sabe.
    Sin esto, cambiar el idioma desde cualquier pantalla que no sea la principal
    te dejaba en la principal, perdiendo lo que estabas leyendo.

    SOLO se aceptan direcciones de esta misma app: si se confiara en lo que manda
    el navegador sin mirar, una web ajena podría usar este botón para llevar a la
    mamá a una página falsa que le pida la clave.
    """
    destino = request.referrer or ''
    raiz = request.host_url.rstrip('/')
    if destino.startswith(raiz + '/'):
        return destino
    return url_for('inicio')


@app.route('/api/lactancia/idioma', methods=['POST'])
def api_lactancia_idioma():
    """Cambia el idioma de la app. Devuelve `recargar` porque los textos de las
    pantallas los arma el servidor: la forma más simple y segura de que quede
    TODO en el idioma nuevo es volver a pedir la página."""
    try:
        elegido = (request.form.get('idioma') or '').strip()
        if elegido not in i18n.IDIOMAS:
            raise ValueError(f"Idioma inválido: {elegido}")
        database.guardar_perfil(idioma=elegido)
        if _es_ajax():
            return jsonify({'ok': True, 'recargar': True})
        return redirect(_volver_a())
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(_volver_a())
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(_volver_a())


@app.route('/api/lactancia/bebe', methods=['POST'])
def api_lactancia_bebe():
    try:
        nombre = (request.form.get('nombre') or '').strip()[:40]
        fnac = (request.form.get('fecha_nacimiento') or '').strip()
        if fnac:
            try:
                nac = datetime.strptime(fnac, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("La fecha de nacimiento debe ser una fecha válida (día/mes/año).")
            if nac > datetime.now().date():
                raise ValueError("La fecha de nacimiento no puede ser futura.")
        database.guardar_perfil(bebe_nombre=nombre, bebe_fecha_nacimiento=fnac)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/<int:id>/reabrir', methods=['POST'])
def api_lactancia_reabrir(id):
    try:
        partida = database.obtener_partida_lactancia(id)
        if partida is None:
            raise ValueError(f"No existe la bolsita {id}.")
        if not partida['motivo_cierre']:
            raise ValueError("La bolsita no está cerrada.")
        database.reabrir_partida_lactancia(id)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/<int:id>/editar', methods=['POST'])
def api_lactancia_editar(id):
    try:
        partida = database.obtener_partida_lactancia(id)
        if partida is None:
            raise ValueError(f"No existe la bolsita {id}.")
        volumen_ml = logica._lac_parsear_volumen(request.form.get('volumen_ml'),
                                                 logica._lac_params())
        notas = (request.form.get('notas') or '').strip()[:200]
        fecha, hora = logica._lac_parsear_extraccion(request.form)
        database.editar_partida_lactancia(id, fecha, hora, volumen_ml, notas)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/<int:id>/eliminar', methods=['POST'])
def api_lactancia_eliminar(id):
    try:
        if database.obtener_partida_lactancia(id) is None:
            raise ValueError(f"No existe la bolsita {id}.")
        database.eliminar_partida_lactancia(id)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': i18n.t(str(e))}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


# =============================================================================
# DESCARGA — la tabla día a día, para abrir en Excel
# =============================================================================
# Un renglón por cada día de vida del bebé (aunque ese día no haya pasado nada),
# así se puede mirar la evolución completa y hacer gráficos aparte.
#
# Detalles que hacen que Excel la abra bien de una:
#   - Empieza con la marca invisible (BOM): sin eso Excel rompe los acentos.
#   - En español el separador es ';' (es lo que espera el Excel en castellano) y
#     en inglés ','.
#   - Las fechas en día/mes/año, como en toda la app.
def _csv_campo(valor, sep):
    """Un valor listo para el CSV: se entrecomilla solo si hace falta."""
    texto = '' if valor is None else str(valor)
    if any(c in texto for c in (sep, '"', '\n', '\r')):
        return '"' + texto.replace('"', '""') + '"'
    return texto


@app.route('/descargar/dia-a-dia.csv')
def descargar_dia_a_dia():
    tabla = logica._lac_dia_a_dia()
    sep = ';' if i18n.idioma_actual() == 'es' else ','

    def dmy(iso):
        d = datetime.strptime(iso, '%Y-%m-%d').date()
        return f"{d.day:02d}/{d.month:02d}/{d.year}"

    encabezados = [
        i18n.t('Fecha'), i18n.t('Día de vida'), i18n.t('Mes de vida'),
        i18n.t('ml extraídos'), i18n.t('ml tomados'), i18n.t('ml descartados'),
    ]
    lineas = [sep.join(_csv_campo(h, sep) for h in encabezados)]
    for f in tabla['filas']:
        lineas.append(sep.join(_csv_campo(v, sep) for v in (
            dmy(f['fecha']), f['dia_vida'], f['mes_vida'],
            f['extraido_ml'], f['tomado_ml'], f['descartado_ml'],
        )))
    t = tabla['totales']
    lineas.append(sep.join(_csv_campo(v, sep) for v in (
        i18n.t('Totales'), '', '',
        t['extraido_ml'], t['tomado_ml'], t['descartado_ml'],
    )))

    csv = '\ufeff' + '\r\n'.join(lineas) + '\r\n'
    nombre = f"{i18n.t('lactancia-dia-a-dia')}-{datetime.now().date().isoformat()}.csv"
    return Response(csv, mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename="{nombre}"',
        'Cache-Control': 'no-store',
    })


# =============================================================================
# PWA — app instalable (manifest + service worker públicos)
# =============================================================================
# Las capturas que muestra la pantalla de instalación de Android y la ficha de
# Google Play. REGLA DURA: todas las de un mismo `form_factor` tienen que tener
# la MISMA proporción, si no Chrome descarta la pantalla linda de instalación
# entera. Y `sizes` tiene que coincidir exacto con los píxeles del archivo o la
# captura se ignora en silencio.
# Se regeneran con: venv\Scripts\python.exe herramientas\generar_capturas.py
_CAPTURAS = [
    ('celular-1-heladera.png', '1080x1920', 'narrow', 'Tu leche guardada, de un vistazo'),
    ('celular-2-cargar.png', '1080x1920', 'narrow', 'Cargar una extracción en dos toques'),
    ('celular-3-resumen.png', '1080x1920', 'narrow', 'Cuánto juntaste y cuánto tomó'),
    ('escritorio-1-heladera.png', '1920x1080', 'wide', 'La heladera y el freezer al día'),
    ('escritorio-2-resumen.png', '1920x1080', 'wide', 'El resumen en la computadora'),
]


@app.route('/manifest.webmanifest')
def manifest():
    marca = config.MARCA
    data = {
        # `id` es la IDENTIDAD de la app para Android y para Chrome. Vale "/" y
        # NO otra cosa: ese es exactamente el valor que el navegador venía
        # calculando solo a partir de start_url. Si se cambia, el sistema toma
        # la app por una distinta y la que las mamás YA tienen instalada queda
        # huérfana. En la práctica es irreversible. No tocar.
        "id": "/",
        "name": "Lactancia — Banco de leche",
        "short_name": "Lactancia",
        "description": "Llevá el stock de tu leche materna: freezer, heladera y avisos de vencimiento.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        # Escalera de respaldo: si un navegador no sabe abrir en ventana propia,
        # prueba la barra mínima y recién después la pestaña normal. No cambia
        # nada de lo que se ve hoy.
        "display_override": ["standalone", "minimal-ui", "browser"],
        "orientation": "portrait",
        "lang": "es-AR",
        "dir": "ltr",
        # Vocabulario estándar del W3C, en minúscula (si no, se ignoran). A
        # propósito SIN "medical": la app anota stock y avisa vencimientos, no
        # diagnostica ni indica tratamientos, y etiquetarla como médica invita
        # un escrutinio en Play que no corresponde. La categoría de la ficha de
        # la tienda se elige aparte en Play Console.
        "categories": ["health", "lifestyle", "utilities"],
        "background_color": marca['fondo_light'],
        "theme_color": marca['theme_light'],
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/static/icons/icon-512-maskable.png", "sizes": "512x512",
             "type": "image/png", "purpose": "maskable"},
        ],
        "screenshots": [
            {"src": f"/static/screenshots/{archivo}", "sizes": medidas,
             "type": "image/png", "form_factor": formato, "label": texto}
            for archivo, medidas, formato, texto in _CAPTURAS
        ],
    }
    # Sin esto, si hay que corregir una medida mal puesta el navegador puede
    # seguir usando el manifiesto viejo justo cuando PWABuilder lo está leyendo.
    return Response(json.dumps(data, ensure_ascii=False),
                    mimetype='application/manifest+json',
                    headers={'Cache-Control': 'no-cache'})


@app.route('/sw.js')
def service_worker():
    resp = send_from_directory(app.static_folder, 'sw.js',
                               mimetype='application/javascript')
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


# =============================================================================
# La app de Google Play (TWA) — prueba de que el sitio y la app son de la misma
# =============================================================================
# Android le pide esta dirección al servidor al abrir la app de la tienda, para
# comprobar que la app y este sitio tienen la misma dueña. Si no la encuentra, o
# la respuesta no es la que espera, la app abre igual pero CON LA BARRA DEL
# NAVEGADOR ARRIBA, como una página cualquiera. No da ningún error: simplemente
# se ve fea.
#
# El contenido lo entrega Google Play recién DESPUÉS de subir el archivo .aab
# (Play vuelve a firmar la app con su propia clave), así que no puede vivir en
# el código. Se pega tal cual en data/assetlinks.json, con copiar y pegar, igual
# que data/correo.json. El paso a paso está en PLAY.md.
#
# Va en data/ y no en el repo por dos motivos: esa carpeta está en .gitignore,
# así que editarla en el servidor nunca puede chocar con un `git pull`; y el
# archivo se pega ENTERO desde Play Console, sin reescribir campos a mano.
@app.route('/.well-known/assetlinks.json')
def assetlinks():
    # La carpeta se lee acá adentro y no arriba porque las pruebas la desvían a
    # una temporal.
    if not os.path.exists(os.path.join(database.DATA_DIR, 'assetlinks.json')):
        # Todavía no se publicó en Play, o falta subir el archivo. Se contesta
        # 404 A PROPÓSITO: inventar un contenido haría que Android fallara la
        # verificación sin que nadie entienda por qué.
        return Response('{"error": "sin configurar"}', status=404,
                        mimetype='application/json')
    resp = send_from_directory(database.DATA_DIR, 'assetlinks.json',
                               mimetype='application/json')
    # Sin esto, una huella mal pegada se queda guardada en el navegador y la
    # corrección tarda en llegar.
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


if __name__ == '__main__':
    # Acá abajo SOLO corre el desarrollo local. PythonAnywhere no pasa por este
    # bloque: importa `app` por WSGI, así que allá queda todo como arriba.
    #
    # El servidor local habla http, y una cookie marcada como segura no se
    # guarda en http: sin apagarla no se podría ni entrar para probar.
    app.config['SESSION_COOKIE_SECURE'] = False
    # 5065 y no 5060: Chrome bloquea el 5060 (lo reserva para telefonía SIP) y
    # devuelve ERR_UNSAFE_PORT sin llegar a abrir la app. Solo aplica al
    # desarrollo local; en PythonAnywhere el puerto lo maneja el servidor.
    app.run(host='127.0.0.1', port=5065, debug=True)
