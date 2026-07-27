# =============================================================================
# test_seguridad.py — Que los datos de cada mamá sean SOLO de ella.
# =============================================================================
# Esta es la prueba que más importa ahora que la app la van a usar varias
# personas. Un error acá no se ve en la pantalla: nadie se entera hasta que una
# mamá abre la app y ve la leche de otra.
# =============================================================================

import pytest

import config
import database
import google_login
from conftest import crear_id, payload, post, uid_de, AJAX


# ── Sin sesión no se entra ───────────────────────────────────────────────────
@pytest.mark.parametrize('url', ['/', '/descargar/dia-a-dia.csv'])
def test_sin_sesion_las_pantallas_mandan_a_la_entrada(flask_app, url):
    r = flask_app.test_client().get(url)
    assert r.status_code == 302
    assert '/bienvenida' in r.headers['Location']


@pytest.mark.parametrize('cabeceras', [AJAX, {}])
def test_sin_sesion_los_botones_reciben_un_aviso_y_no_una_pantalla(flask_app, cabeceras):
    # Si la app le contestara la pantalla de bienvenida al JavaScript, la acción
    # fallaría en silencio y la mamá vería un error incomprensible. Vale tanto
    # con la cabecera del JS como sin ella: todo lo que empieza con /api/ es
    # para el JavaScript, nunca para mirar en el navegador.
    r = flask_app.test_client().get('/api/lactancia', headers=cabeceras)
    assert r.status_code == 401
    datos = r.get_json()
    assert datos['sesion_cerrada'] is True
    assert datos['error']


@pytest.mark.parametrize('url', [
    '/api/lactancia/crear', '/api/lactancia/freezar',
    '/api/lactancia/1/cerrar', '/api/lactancia/1/editar',
    '/api/lactancia/1/eliminar', '/api/lactancia/1/reabrir',
    '/api/lactancia/1/bajar', '/api/lactancia/config',
    '/api/lactancia/bebe', '/api/lactancia/recordatorio',
])
def test_sin_sesion_ninguna_accion_se_ejecuta(flask_app, url):
    r = flask_app.test_client().post(url, headers=AJAX)
    assert r.status_code == 401


def test_las_pantallas_de_entrada_si_son_publicas(flask_app):
    c = flask_app.test_client()
    for url in ('/bienvenida', '/login', '/registro', '/manifest.webmanifest', '/sw.js'):
        assert c.get(url).status_code == 200, url


def test_al_salir_se_cierra_la_sesion_de_verdad(cliente):
    assert cliente.get('/salir').status_code == 302
    assert uid_de(cliente) is None
    assert cliente.get('/api/lactancia', headers=AJAX).status_code == 401


# ── LA PRUEBA ESTRELLA: una mamá no puede tocar la leche de otra ─────────────
def test_dos_mamas_tienen_bases_distintas(cliente, cliente_2):
    assert uid_de(cliente) != uid_de(cliente_2)
    crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    assert len(payload(cliente)['freezer']) == 1
    assert payload(cliente_2)['freezer'] == []      # la otra no ve nada


def test_una_mama_no_puede_cerrar_usar_ni_borrar_la_leche_de_otra(cliente, cliente_2):
    ajeno = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    antes = payload(cliente)

    for url, campos in (
        (f'/api/lactancia/{ajeno}/cerrar',   {'motivo': 'usada'}),
        (f'/api/lactancia/{ajeno}/editar',   {'volumen_ml': 1,
                                              'fecha_extraccion': '2026-01-01',
                                              'hora_extraccion': '08:00'}),
        (f'/api/lactancia/{ajeno}/eliminar', {}),
        (f'/api/lactancia/{ajeno}/reabrir',  {}),
        (f'/api/lactancia/{ajeno}/bajar',    {}),
        ('/api/lactancia/freezar',           {'ids': str(ajeno)}),
    ):
        r = post(cliente_2, url, **campos)
        assert r.status_code == 400, url          # rebota con un error limpio
        assert r.get_json()['ok'] is False, url

    # Y lo más importante: la leche de la primera mamá quedó EXACTAMENTE igual.
    assert payload(cliente)['freezer'] == antes['freezer']
    assert payload(cliente_2)['freezer'] == []


def test_la_configuracion_de_una_mama_no_le_cambia_los_tiempos_a_la_otra(cliente, cliente_2):
    post(cliente, '/api/lactancia/config', freezer_meses=12)
    assert payload(cliente)['params']['freezer_meses'] == 12
    assert payload(cliente_2)['params']['freezer_meses'] == 6    # sigue en fábrica


def test_el_bebe_de_una_mama_no_aparece_en_la_app_de_la_otra(cliente, cliente_2):
    post(cliente, '/api/lactancia/bebe', nombre='León', fecha_nacimiento='2026-05-14')
    assert payload(cliente)['bebe']['nombre'] == 'León'
    assert payload(cliente_2)['bebe']['nombre'] == 'el bebé'


# ── Crear cuenta e iniciar sesión ────────────────────────────────────────────
def test_la_clave_nunca_se_guarda_tal_cual_se_escribio(flask_app):
    c = flask_app.test_client()
    r = c.post('/registro', data={'email': 'mama@ejemplo.com',
                                  'password': 'secreta123', 'password2': 'secreta123'})
    assert r.status_code == 302              # entró

    conn = database.conectar_usuarios()
    fila = conn.execute('SELECT * FROM usuarios WHERE email = ?',
                        ('mama@ejemplo.com',)).fetchone()
    conn.close()
    guardado = fila['password_hash']
    assert 'secreta123' not in guardado      # ni un pedacito en texto plano
    assert len(guardado) > 40                # es un hash, no la clave


@pytest.mark.parametrize('datos', [
    {'email': 'sin-arroba', 'password': 'secreta123', 'password2': 'secreta123'},
    {'email': 'mama@', 'password': 'secreta123', 'password2': 'secreta123'},
    {'email': '', 'password': 'secreta123', 'password2': 'secreta123'},
    {'email': 'ok@ejemplo.com', 'password': '12345', 'password2': '12345'},   # muy corta
    {'email': 'ok@ejemplo.com', 'password': 'secreta123', 'password2': 'otra'},
])
def test_un_registro_mal_hecho_no_crea_ninguna_cuenta(flask_app, datos):
    c = flask_app.test_client()
    r = c.post('/registro', data=datos)
    assert r.status_code == 200               # se queda en la pantalla, con el error
    with c.session_transaction() as s:
        assert 'uid' not in s                 # y NO quedó adentro


def test_no_se_pueden_crear_dos_cuentas_con_el_mismo_mail(flask_app):
    datos = {'email': 'repetida@ejemplo.com', 'password': 'secreta123',
             'password2': 'secreta123'}
    assert flask_app.test_client().post('/registro', data=datos).status_code == 302
    r = flask_app.test_client().post('/registro', data=datos)
    assert r.status_code == 200
    assert 'uid' not in r.request.cookies     # no entró


def test_con_la_clave_equivocada_no_se_entra(flask_app):
    flask_app.test_client().post('/registro', data={
        'email': 'login@ejemplo.com', 'password': 'secreta123',
        'password2': 'secreta123'})

    c = flask_app.test_client()
    r = c.post('/login', data={'email': 'login@ejemplo.com', 'password': 'equivocada'})
    assert r.status_code == 200
    with c.session_transaction() as s:
        assert 'uid' not in s

    r = c.post('/login', data={'email': 'login@ejemplo.com', 'password': 'secreta123'})
    assert r.status_code == 302
    with c.session_transaction() as s:
        assert s['uid']


def test_un_mail_que_no_existe_no_delata_que_no_existe(flask_app):
    # El mensaje es el mismo que con la clave equivocada: así nadie puede usar
    # la pantalla de entrada para averiguar qué mails están registrados.
    c = flask_app.test_client()
    r = c.post('/login', data={'email': 'nadie@ejemplo.com', 'password': 'loquesea'})
    assert 'incorrect' in r.get_data(as_text=True).lower() \
        or 'incorrecto' in r.get_data(as_text=True).lower()


# ── Texto peligroso en las notas ─────────────────────────────────────────────
def test_una_nota_con_codigo_no_se_ejecuta_en_la_pantalla(cliente):
    veneno = '</script><script>alert(1)</script>'
    crear_id(cliente, ubicacion='freezer', volumen_ml=100, notas=veneno)

    html = cliente.get('/').get_data(as_text=True)
    # El texto tiene que estar guardado tal cual (no se le censura nada a la
    # mamá), pero al escribirlo en la página no puede quedar como código vivo.
    assert '</script><script>alert(1)</script>' not in html
    assert payload(cliente)['freezer'][0]['notas'] == veneno


# ── La lista blanca del perfil ───────────────────────────────────────────────
def test_solo_se_pueden_guardar_los_campos_permitidos_del_perfil(usuaria):
    # guardar_perfil arma el SQL con los nombres de los campos. La lista blanca
    # es lo único que impide que un nombre inventado llegue a la base.
    database.guardar_perfil(bebe_nombre='León', password_hash='inventado',
                            tabla_secreta='x')
    perfil = database.obtener_perfil()
    assert perfil['bebe_nombre'] == 'León'
    assert 'password_hash' not in perfil


def test_un_nombre_de_campo_con_sql_adentro_se_ignora(usuaria):
    database.guardar_perfil(**{"idioma='en', bebe_nombre='hackeado' --": 1})
    assert database.obtener_perfil()['bebe_nombre'] != 'hackeado'
    # Y la tabla sigue entera.
    assert database.obtener_perfil()['id'] == 1


# ── Entrar con Google ────────────────────────────────────────────────────────
def _pase(**cambios):
    """Un pase de Google válido, al que se le puede romper un campo a propósito."""
    datos = {
        'aud': config.GOOGLE_CLIENT_ID,
        'iss': 'https://accounts.google.com',
        'exp': '99999999999',
        'sub': '1234567890',
        'email': 'mama@gmail.com',
        'email_verified': 'true',
        'name': 'Mariana',
        'picture': 'https://lh3.googleusercontent.com/foto.jpg',
    }
    datos.update(cambios)
    return datos


@pytest.fixture
def google_dice(monkeypatch):
    """Simula la respuesta de Google, sin salir a internet."""
    def _configurar(datos):
        monkeypatch.setattr(google_login, '_consultar_a_google', lambda _t: datos)
    return _configurar


def test_un_pase_de_google_correcto_se_acepta(google_dice):
    google_dice(_pase())
    info = google_login.verificar_id_token('pase-de-mentira')
    assert info == {'sub': '1234567890', 'email': 'mama@gmail.com',
                    'nombre': 'Mariana',
                    'foto': 'https://lh3.googleusercontent.com/foto.jpg'}


def test_un_pase_emitido_para_OTRA_app_se_rechaza(google_dice):
    # Este es el control clave: un pase auténtico de Google, pero de otra
    # aplicación, no puede servir para entrar acá.
    google_dice(_pase(aud='otra-app.apps.googleusercontent.com'))
    with pytest.raises(google_login.ErrorGoogle):
        google_login.verificar_id_token('pase-de-mentira')


@pytest.mark.parametrize('roto', [
    {'iss': 'accounts.google.com.falso.net'},   # no lo firmó Google
    {'exp': '1000000000'},                      # venció (año 2001)
    {'exp': 'nunca'},                           # ni siquiera es una fecha
    {'sub': ''},                                # sin identificador de persona
])
def test_un_pase_de_google_adulterado_se_rechaza(google_dice, roto):
    google_dice(_pase(**roto))
    with pytest.raises(google_login.ErrorGoogle):
        google_login.verificar_id_token('pase-de-mentira')


def test_si_google_no_confirma_el_mail_no_se_usa_ese_mail(google_dice):
    # Sin esto, alguien podría entrar con un mail ajeno y quedarse con la cuenta
    # de otra mamá que se había registrado con ese mismo mail.
    google_dice(_pase(email_verified='false'))
    assert google_login.verificar_id_token('pase-de-mentira')['email'] is None


def test_un_pase_vacio_o_gigante_se_rechaza_sin_preguntarle_a_google():
    for malo in ('', None, 'x' * 9000):
        with pytest.raises(google_login.ErrorGoogle):
            google_login.verificar_id_token(malo)


@pytest.mark.parametrize('url,esperado', [
    ('https://lh3.googleusercontent.com/f.jpg', 'https://lh3.googleusercontent.com/f.jpg'),
    ('https://googleusercontent.com/f.jpg',     'https://googleusercontent.com/f.jpg'),
    ('http://lh3.googleusercontent.com/f.jpg',  None),   # sin https
    ('https://googleusercontent.com.malo.net/f.jpg', None),   # dominio disfrazado
    ('https://otrositio.com/f.jpg',             None),
    ('', None),
    (None, None),
])
def test_la_foto_de_perfil_solo_puede_venir_de_google(url, esperado):
    assert google_login._foto_valida(url) == esperado


def test_el_pedido_de_google_solo_se_acepta_desde_nuestra_propia_pagina(flask_app):
    # Sin la cabecera, cualquier web ajena podría hacerle enviar este pedido al
    # navegador de la mamá.
    r = flask_app.test_client().post('/auth/google', json={'credential': 'x'})
    assert r.status_code == 400


def test_una_invitada_que_entra_con_google_se_lleva_su_leche(cliente, google_dice):
    # Decisión de producto: lo que cargó sin cuenta tiene que seguir estando
    # cuando se crea la cuenta. Es la que más se nota si se rompe.
    uid_antes = uid_de(cliente)
    crear_id(cliente, ubicacion='freezer', volumen_ml=100)

    google_dice(_pase(sub='invitada-que-se-registra', email='nueva@gmail.com'))
    r = cliente.post('/auth/google', json={'credential': 'pase'}, headers=AJAX)
    assert r.status_code == 200 and r.get_json()['ok']

    assert uid_de(cliente) == uid_antes                   # es la misma usuaria
    assert len(payload(cliente)['freezer']) == 1          # con su leche intacta
    assert database.obtener_usuario(uid_antes)['tipo'] == 'cuenta'
