# =============================================================================
# test_validaciones.py — Que la app no acepte cualquier cosa.
# =============================================================================
# Todo lo que una mamá escribe en un formulario pasa por estas funciones antes
# de guardarse. Si dejan pasar un dato imposible (200 litros, una extracción de
# mañana), ese dato queda en la base para siempre y ensucia todas las cuentas.
# =============================================================================

from datetime import date, timedelta

import pytest

import app as app_modulo
import logica
from conftest import params_base

HOY = date.today()
AYER = (HOY - timedelta(days=1)).isoformat()
MANANA = (HOY + timedelta(days=1)).isoformat()


# ── El volumen en ml ─────────────────────────────────────────────────────────
def test_un_volumen_normal_se_acepta():
    assert logica._lac_parsear_volumen('120') == 120
    assert logica._lac_parsear_volumen(' 120 ') == 120


@pytest.mark.parametrize('valor', ['0', '-5', '2001', '99999'])
def test_se_rechaza_un_volumen_fuera_de_lo_posible(valor):
    with pytest.raises(ValueError):
        logica._lac_parsear_volumen(valor)


@pytest.mark.parametrize('valor', ['', 'cien', '12,5', '12.5', None])
def test_se_rechaza_un_volumen_que_no_es_un_numero_entero(valor):
    with pytest.raises(ValueError):
        logica._lac_parsear_volumen(valor)


def test_con_la_capacidad_de_bolsita_activada_no_se_puede_cargar_de_mas():
    params = params_base(bolsa_capacidad_activa=True, bolsa_capacidad_ml=150)
    assert logica._lac_parsear_volumen('150', params) == 150      # justo, entra
    with pytest.raises(ValueError):
        logica._lac_parsear_volumen('151', params)


def test_con_la_capacidad_apagada_el_tope_de_la_bolsita_no_molesta():
    params = params_base(bolsa_capacidad_activa=False, bolsa_capacidad_ml=150)
    assert logica._lac_parsear_volumen('400', params) == 400


# ── Fecha y hora de extracción ───────────────────────────────────────────────
def test_una_extraccion_de_ayer_se_acepta():
    assert logica._lac_parsear_extraccion(
        {'fecha_extraccion': AYER, 'hora_extraccion': '08:00'}) == (AYER, '08:00')


def test_no_se_puede_cargar_una_extraccion_del_futuro():
    with pytest.raises(ValueError):
        logica._lac_parsear_extraccion(
            {'fecha_extraccion': MANANA, 'hora_extraccion': '08:00'})


@pytest.mark.parametrize('form', [
    {'fecha_extraccion': '01/07/2026', 'hora_extraccion': '08:00'},   # formato al revés
    {'fecha_extraccion': '2026-13-01', 'hora_extraccion': '08:00'},   # mes 13
    {'fecha_extraccion': '', 'hora_extraccion': '08:00'},             # vacía
    {'fecha_extraccion': '2026-02-30', 'hora_extraccion': '08:00'},   # día que no existe
])
def test_se_rechaza_una_fecha_de_extraccion_invalida(form):
    with pytest.raises(ValueError):
        logica._lac_parsear_extraccion(form)


@pytest.mark.parametrize('hora', ['', '8', '25:00', '08:70', 'mañana'])
def test_se_rechaza_una_hora_de_extraccion_invalida(hora):
    with pytest.raises(ValueError):
        logica._lac_parsear_extraccion({'fecha_extraccion': AYER,
                                        'hora_extraccion': hora})


# ── Fecha de cierre (cuando se usa o se descarta una bolsita) ────────────────
def test_sin_fecha_de_cierre_se_toma_hoy():
    assert logica._lac_parsear_fecha_cierre('') == HOY.isoformat()
    assert logica._lac_parsear_fecha_cierre(None) == HOY.isoformat()


def test_no_se_puede_cerrar_una_bolsita_con_fecha_futura():
    with pytest.raises(ValueError):
        logica._lac_parsear_fecha_cierre(MANANA)


def test_se_rechaza_una_fecha_de_cierre_con_formato_raro():
    with pytest.raises(ValueError):
        logica._lac_parsear_fecha_cierre('ayer')


# ── El formulario de alta completo ───────────────────────────────────────────
def test_el_alta_devuelve_los_datos_listos_para_guardar():
    datos = logica._lac_leer_form_alta({
        'ubicacion': 'heladera', 'volumen_ml': '90',
        'fecha_extraccion': AYER, 'hora_extraccion': '07:15',
        'notas': '  con grasa arriba  ',
    })
    assert datos == {'ubicacion': 'heladera', 'fecha_extraccion': AYER,
                     'hora_extraccion': '07:15', 'volumen_ml': 90,
                     'notas': 'con grasa arriba'}


@pytest.mark.parametrize('ubicacion', ['', 'alacena', 'FREEZER', 'freezer '])
def test_solo_existen_freezer_y_heladera(ubicacion):
    with pytest.raises(ValueError):
        logica._lac_leer_form_alta({'ubicacion': ubicacion, 'volumen_ml': '90',
                                    'fecha_extraccion': AYER,
                                    'hora_extraccion': '07:15'})


def test_una_nota_larguisima_se_recorta_a_200_caracteres():
    # Sin este recorte, un texto enorme entraría a la base y rompería el diseño
    # de las tarjetas en el celular.
    datos = logica._lac_leer_form_alta({
        'ubicacion': 'freezer', 'volumen_ml': '90',
        'fecha_extraccion': AYER, 'hora_extraccion': '07:15',
        'notas': 'a' * 300,
    })
    assert len(datos['notas']) == 200


# ── El texto de "cuánto falta" ───────────────────────────────────────────────
def test_las_horas_se_escriben_en_criollo():
    assert app_modulo._horas_texto(0.5) == '30 min'
    assert app_modulo._horas_texto(2) == '2 h'
    assert app_modulo._horas_texto(2 + 20 / 60) == '2 h 20 min'
    # Un ratito mínimo nunca se muestra como "0 min".
    assert app_modulo._horas_texto(0.001) == '1 min'
