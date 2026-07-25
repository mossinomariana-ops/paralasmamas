# =============================================================================
# app.py — App Lactancia (banco de leche materna) · Flask · multiusuario.
# =============================================================================
# App independiente para que cada mamá lleve su stock de leche. Extraída del
# módulo Lactancia del fondo familiar, sin nada de gastos/calendario/rutina.
# Cada usuaria (invitada o con cuenta) tiene su propia base y arranca vacía.
# =============================================================================

import os
import json
import secrets
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for, jsonify,
    session, send_from_directory, Response
)

import config
import database
import logica
from auth import init_auth

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

init_auth(app)


def _es_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _static_version():
    """mtime más reciente de los estáticos principales → cache-busting."""
    try:
        paths = [os.path.join(app.static_folder, n)
                 for n in ('style.css', 'lactancia.js', 'pwa.js')]
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
        },
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


@app.route('/api/lactancia')
def api_lactancia():
    return jsonify({'ok': True, **logica._lac_payload()})


@app.route('/api/lactancia/crear', methods=['POST'])
def api_lactancia_crear():
    try:
        datos = logica._lac_leer_form_alta(request.form)
        database.agregar_partida_lactancia(**datos)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 400
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
            raise ValueError(f"No existe la partida {id}.")
        if partida['motivo_cierre']:
            raise ValueError("La partida ya está cerrada.")

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
                        "(lo que tenía la bolsa).")

        database.cerrar_partida_lactancia(id, motivo, fecha_cierre, notas, consumido_ml)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 400
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
            raise ValueError("Tildá al menos una partida de heladera para freezar.")

        confirmar_vencidas = request.form.get('confirmar_vencidas') == '1'
        partidas = []
        vencidas = 0
        for pid in ids:
            row = database.obtener_partida_lactancia(pid)
            if row is None:
                raise ValueError(f"No existe la partida {pid}.")
            p = dict(row)
            if p['ubicacion'] != 'heladera':
                raise ValueError("Solo se freezan partidas de heladera.")
            if p['motivo_cierre']:
                raise ValueError("Una de las partidas tildadas ya está cerrada.")
            if not logica._lac_freezable(p, params, ahora):
                vencidas += 1
            partidas.append(p)

        if vencidas and not confirmar_vencidas:
            raise ValueError(
                "Hay partidas vencidas entre las tildadas: confirmá que se pasaron "
                "al freezer antes de vencerse para poder freezarlas.")

        volumen_ml = sum(p['volumen_ml'] for p in partidas)
        if volumen_ml > 2000:
            raise ValueError("El volumen combinado supera los 2000 ml; freezá en tandas.")

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
            return jsonify({'ok': False, 'error': str(e)}), 400
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
            return jsonify({'ok': False, 'error': str(e)}), 400
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
            raise ValueError("La hora del recordatorio debe ser HH:MM (ej. 21:00).")
        database.guardar_perfil(recordatorio_activo=1 if activo else 0,
                                recordatorio_hora=hora)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


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
            return jsonify({'ok': False, 'error': str(e)}), 400
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
            raise ValueError(f"No existe la partida {id}.")
        if not partida['motivo_cierre']:
            raise ValueError("La partida no está cerrada.")
        database.reabrir_partida_lactancia(id)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 400
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
            raise ValueError(f"No existe la partida {id}.")
        volumen_ml = logica._lac_parsear_volumen(request.form.get('volumen_ml'))
        notas = (request.form.get('notas') or '').strip()[:200]
        fecha, hora = logica._lac_parsear_extraccion(request.form)
        database.editar_partida_lactancia(id, fecha, hora, volumen_ml, notas)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


@app.route('/api/lactancia/<int:id>/eliminar', methods=['POST'])
def api_lactancia_eliminar(id):
    try:
        if database.obtener_partida_lactancia(id) is None:
            raise ValueError(f"No existe la partida {id}.")
        database.eliminar_partida_lactancia(id)
        if _es_ajax():
            return jsonify({'ok': True, **logica._lac_payload()})
        return redirect(url_for('inicio'))
    except ValueError as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 400
        return redirect(url_for('inicio'))
    except Exception as e:
        if _es_ajax():
            return jsonify({'ok': False, 'error': str(e)}), 500
        return redirect(url_for('inicio'))


# =============================================================================
# PWA — app instalable (manifest + service worker públicos)
# =============================================================================
@app.route('/manifest.webmanifest')
def manifest():
    pal = config.PALETA_LIGHT
    data = {
        "name": "Lactancia — Banco de leche",
        "short_name": "Lactancia",
        "description": "Llevá el stock de tu leche materna: freezer, heladera y avisos de vencimiento.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "lang": "es-AR",
        "background_color": pal['fondo'],
        "theme_color": pal['acento'],
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/static/icons/icon-512-maskable.png", "sizes": "512x512",
             "type": "image/png", "purpose": "maskable"},
        ],
    }
    return Response(json.dumps(data, ensure_ascii=False),
                    mimetype='application/manifest+json')


@app.route('/sw.js')
def service_worker():
    resp = send_from_directory(app.static_folder, 'sw.js',
                               mimetype='application/javascript')
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5060, debug=True)
