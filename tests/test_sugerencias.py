# =============================================================================
# test_sugerencias.py — La tarjeta de Sugerencias (mail anónimo a la app).
# =============================================================================
# Nada de esto manda correo de verdad: `correo.enviar` se reemplaza por una
# función de mentira que anota lo que le habrían pedido enviar.
#
# Lo importante que se cuida acá:
#   - La sugerencia es ANÓNIMA: en el mail no viaja quién la escribió.
#   - Como el servidor NO guarda copia (decisión de Mari), si el envío falla la
#     app tiene que avisarlo con un error, nunca decir que salió.
# =============================================================================

import pytest

import app as app_modulo
import correo

from conftest import AJAX, post


@pytest.fixture
def correo_falso(monkeypatch):
    """Reemplaza el envío real y deja a mano lo que se habría mandado."""
    enviados = []

    def _enviar(asunto, cuerpo, responder_a=None):
        enviados.append({'asunto': asunto, 'cuerpo': cuerpo, 'responder_a': responder_a})
        return True

    monkeypatch.setattr(correo, 'activo', lambda: True)
    monkeypatch.setattr(correo, 'enviar', _enviar)
    return enviados


def _sug(cliente, **campos):
    return post(cliente, '/api/lactancia/sugerencia', **campos)


def test_se_manda_y_el_texto_llega_entero(cliente, correo_falso):
    r = _sug(cliente, texto='Estaría bueno poder anotar el pecho de cada extracción')
    assert r.status_code == 200 and r.get_json()['ok'] is True
    assert len(correo_falso) == 1
    assert 'anotar el pecho' in correo_falso[0]['cuerpo']


def test_es_anonima_no_viaja_quien_la_escribio(cliente, correo_falso):
    with cliente.session_transaction() as s:
        uid = s['uid']
    _sug(cliente, texto='Una idea')
    cuerpo = correo_falso[0]['cuerpo']

    # Ni el id de la usuaria ni el nombre de su base aparecen en el mail.
    assert f'u_{uid}' not in cuerpo
    assert 'uid' not in cuerpo.lower()

    # El pie del mail solo puede tener el contexto acordado: cuándo se mandó,
    # el idioma, si entró como invitada o con cuenta, y el correo que ella misma
    # haya tipeado. Ni una línea más.
    pie = cuerpo.split('---\n', 1)[1].strip().splitlines()
    assert len(pie) == 3, pie
    assert pie[0].startswith('Enviada desde la app Lactancia el ')
    assert pie[1].startswith('Idioma:') and 'Entró como: invitada' in pie[1]
    assert pie[2] == 'Correo de contacto: (no dejó)'


def test_el_correo_opcional_queda_como_responder_a(cliente, correo_falso):
    _sug(cliente, texto='Otra idea', email='mama@ejemplo.com')
    assert correo_falso[0]['responder_a'] == 'mama@ejemplo.com'


def test_sin_correo_de_contacto_no_hay_responder_a(cliente, correo_falso):
    _sug(cliente, texto='Sin contacto')
    assert correo_falso[0]['responder_a'] is None


def test_vacia_no_se_manda(cliente, correo_falso):
    r = _sug(cliente, texto='   ')
    assert r.status_code == 400
    assert r.get_json()['error']
    assert correo_falso == []


def test_correo_mal_escrito_se_rechaza(cliente, correo_falso):
    r = _sug(cliente, texto='Una idea', email='esto-no-es-un-mail')
    assert r.status_code == 400
    assert correo_falso == []


def test_si_el_envio_falla_la_app_avisa_y_no_dice_que_salio(cliente, monkeypatch):
    """Es la prueba clave del diseño elegido: como no se guarda copia, un fallo
    silencioso significaría perder lo que la mamá escribió."""
    def _explota(asunto, cuerpo, responder_a=None):
        raise RuntimeError("No pudimos conectarnos al servidor de correo.")

    monkeypatch.setattr(correo, 'activo', lambda: True)
    monkeypatch.setattr(correo, 'enviar', _explota)

    r = _sug(cliente, texto='Una idea que no se tiene que perder')
    assert r.status_code == 502
    datos = r.get_json()
    assert datos['ok'] is False
    assert datos['error']


def test_si_falla_se_puede_reintentar_en_el_momento(cliente, monkeypatch):
    """El freno anti-spam no puede dejarla esperando un minuto por un envío que
    NO salió."""
    def _explota(asunto, cuerpo, responder_a=None):
        raise RuntimeError("No pudimos conectarnos al servidor de correo.")

    monkeypatch.setattr(correo, 'activo', lambda: True)
    monkeypatch.setattr(correo, 'enviar', _explota)
    assert _sug(cliente, texto='Intento 1').status_code == 502

    enviados = []
    monkeypatch.setattr(correo, 'enviar',
                        lambda a, c, responder_a=None: enviados.append(c))
    r = _sug(cliente, texto='Intento 2')
    assert r.status_code == 200 and len(enviados) == 1


def test_dos_seguidas_se_frenan(cliente, correo_falso):
    assert _sug(cliente, texto='Primera').status_code == 200
    r = _sug(cliente, texto='Segunda al toque')
    assert r.status_code == 400
    assert len(correo_falso) == 1


def test_sin_casilla_configurada_la_tarjeta_no_se_dibuja(cliente, monkeypatch):
    monkeypatch.setattr(correo, 'activo', lambda: False)
    html = cliente.get('/').get_data(as_text=True)
    assert 'lac-sug-enviar' not in html

    r = _sug(cliente, texto='Una idea')
    assert r.status_code == 400


def test_con_casilla_configurada_la_tarjeta_aparece(cliente, correo_falso):
    html = cliente.get('/').get_data(as_text=True)
    assert 'lac-sug-enviar' in html


def test_la_clave_de_correo_no_se_filtra_a_la_pantalla(cliente, monkeypatch):
    """La contraseña de aplicación vive en data/correo.json y nunca puede
    aparecer en el HTML que ve la usuaria."""
    monkeypatch.setattr(correo, 'config',
                        lambda: {'usuario': 'app@gmail.com',
                                 'clave': 'clave-super-secreta',
                                 'destino': 'mari@gmail.com'})
    html = cliente.get('/').get_data(as_text=True)
    assert 'clave-super-secreta' not in html
    assert 'app@gmail.com' not in html
