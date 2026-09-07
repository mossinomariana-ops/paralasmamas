# =============================================================================
# test_vencimientos.py — El corazón de la app.
# =============================================================================
# Si algo de este archivo falla, la app le puede decir a una mamá que una leche
# está bien cuando ya venció. Es la prueba más importante de todas.
#
# Todo lo de acá son funciones puras: no tocan la base de datos ni la pantalla.
# Se les dan datos inventados y una fecha "ahora" fija, así el resultado no
# depende de cuándo se corran las pruebas.
# =============================================================================

from datetime import date, datetime

import pytest

import logica
from conftest import params_base


# ── Sumar meses a una fecha ──────────────────────────────────────────────────
# Es el cálculo que decide el vencimiento del freezer. El caso peligroso es el
# día 31: "31 de enero + 1 mes" no existe, y hay que decidir qué se hace.
def test_31_de_enero_mas_un_mes_cae_el_ultimo_dia_de_febrero():
    assert logica._act_sumar_intervalo(date(2026, 1, 31), 1, 'meses') == date(2026, 2, 28)


def test_en_anio_bisiesto_el_31_de_enero_cae_el_29_de_febrero():
    assert logica._act_sumar_intervalo(date(2024, 1, 31), 1, 'meses') == date(2024, 2, 29)


def test_31_de_marzo_mas_un_mes_cae_el_30_de_abril():
    assert logica._act_sumar_intervalo(date(2026, 3, 31), 1, 'meses') == date(2026, 4, 30)


def test_sumar_meses_cruzando_el_fin_de_anio():
    assert logica._act_sumar_intervalo(date(2026, 8, 20), 6, 'meses') == date(2027, 2, 20)


def test_sumar_dias_semanas_y_anios():
    assert logica._act_sumar_intervalo(date(2026, 1, 1), 10, 'dias') == date(2026, 1, 11)
    assert logica._act_sumar_intervalo(date(2026, 1, 1), 2, 'semanas') == date(2026, 1, 15)
    # 29 de febrero + 1 año tampoco existe: cae el 28.
    assert logica._act_sumar_intervalo(date(2024, 2, 29), 1, 'anios') == date(2025, 2, 28)


def test_una_unidad_que_no_existe_da_error():
    with pytest.raises(ValueError):
        logica._act_sumar_intervalo(date(2026, 1, 1), 1, 'lunas')


# ── El momento exacto de la extracción ───────────────────────────────────────
def test_extraccion_con_hora():
    p = {'fecha_extraccion': '2026-07-01', 'hora_extraccion': '14:30'}
    assert logica._lac_extraccion_dt(p) == datetime(2026, 7, 1, 14, 30)


def test_extraccion_sin_hora_se_toma_como_medianoche():
    # Es el criterio conservador: la leche "empieza a contar" lo antes posible.
    assert logica._lac_extraccion_dt({'fecha_extraccion': '2026-07-01',
                                      'hora_extraccion': ''}) == datetime(2026, 7, 1)
    assert logica._lac_extraccion_dt({'fecha_extraccion': '2026-07-01',
                                      'hora_extraccion': None}) == datetime(2026, 7, 1)


# ── El vencimiento, en sus tres formas ───────────────────────────────────────
def test_vencimiento_de_freezer_son_meses_desde_la_extraccion_y_vence_al_final_del_dia():
    p = {'ubicacion': 'freezer', 'fecha_extraccion': '2026-01-31'}
    venc = logica._lac_vencimiento(p, params_base(freezer_meses=6))
    assert venc == datetime(2026, 7, 31, 23, 59, 59)


def test_vencimiento_de_heladera_son_horas_desde_la_extraccion():
    p = {'ubicacion': 'heladera', 'fecha_extraccion': '2026-07-01',
         'hora_extraccion': '08:00', 'tipo': 'fresca'}
    venc = logica._lac_vencimiento(p, params_base(heladera_horas=48))
    assert venc == datetime(2026, 7, 3, 8, 0)


def test_vencimiento_de_descongelada_cuenta_desde_que_se_bajo_del_freezer():
    # Lo importante: NO cuenta desde la extracción (que puede ser de hace meses)
    # sino desde `cargada`, el momento en que se la bajó a la heladera.
    p = {'ubicacion': 'heladera', 'tipo': 'descongelada',
         'fecha_extraccion': '2026-01-15', 'hora_extraccion': '08:00',
         'cargada': '2026-07-01T10:00:00'}
    venc = logica._lac_vencimiento(p, params_base(descongelada_horas=24))
    assert venc == datetime(2026, 7, 2, 10, 0)


# ── El estado: disponible / vence pronto / vencida ───────────────────────────
def test_una_partida_cerrada_muestra_su_cierre_aunque_este_vencida():
    # El cierre manual gana sobre todo lo demás: si la mamá ya la usó, la app
    # tiene que decir "usada", no "vencida".
    p = {'ubicacion': 'freezer', 'fecha_extraccion': '2020-01-01',
         'motivo_cierre': 'usada'}
    assert logica._lac_estado(p, params_base(), datetime(2026, 7, 1)) == 'usada'


def test_freezer_pasada_la_fecha_esta_vencida():
    p = {'ubicacion': 'freezer', 'fecha_extraccion': '2026-01-01'}
    params = params_base(freezer_meses=6)   # vence el 1/7/2026 a las 23:59:59
    assert logica._lac_estado(p, params, datetime(2026, 7, 2, 0, 1)) == 'vencida'
    # Un minuto antes del final del día todavía sirve.
    assert logica._lac_estado(p, params, datetime(2026, 7, 1, 23, 0)) != 'vencida'


def test_freezer_avisa_justo_cuando_faltan_los_dias_configurados():
    p = {'ubicacion': 'freezer', 'fecha_extraccion': '2026-01-01'}
    params = params_base(freezer_meses=6, aviso_freezer_dias=14)  # vence el 1/7
    # Faltan exactamente 14 días → ya tiene que avisar.
    assert logica._lac_estado(p, params, datetime(2026, 6, 17, 10, 0)) == 'vence_pronto'
    # Faltan 15 → todavía no.
    assert logica._lac_estado(p, params, datetime(2026, 6, 16, 10, 0)) == 'disponible'


# ── El back up del jardín ────────────────────────────────────────────────────
# La bolsita que Mari deja en el freezer del jardín maternal sigue estando bien y
# sigue siendo stock: lo único que cambia es que no la tiene en casa. Por eso la
# marca reemplaza solo a "disponible" y JAMÁS puede tapar un aviso de
# vencimiento: si se está por vencer, hay que ir a buscarla.
def test_una_bolsita_del_jardin_dice_que_esta_en_el_jardin():
    p = {'ubicacion': 'freezer', 'fecha_extraccion': '2026-01-01', 'en_jardin': 1}
    params = params_base(freezer_meses=6, aviso_freezer_dias=14)  # vence el 1/7
    assert logica._lac_estado(p, params, datetime(2026, 2, 1, 10, 0)) == 'en_jardin'


def test_el_aviso_de_vencimiento_le_gana_a_la_marca_del_jardin():
    p = {'ubicacion': 'freezer', 'fecha_extraccion': '2026-01-01', 'en_jardin': 1}
    params = params_base(freezer_meses=6, aviso_freezer_dias=14)  # vence el 1/7
    assert logica._lac_estado(p, params, datetime(2026, 6, 17, 10, 0)) == 'vence_pronto'
    assert logica._lac_estado(p, params, datetime(2026, 7, 2, 0, 1)) == 'vencida'


def test_una_bolsita_del_jardin_ya_cerrada_muestra_su_cierre():
    p = {'ubicacion': 'freezer', 'fecha_extraccion': '2026-01-01', 'en_jardin': 1,
         'motivo_cierre': 'usada'}
    assert logica._lac_estado(p, params_base(), datetime(2026, 2, 1)) == 'usada'


def test_sin_la_marca_la_bolsita_sigue_estando_disponible():
    # Las bolsitas viejas, anteriores a la columna, llegan con el campo en None.
    for marca in (None, 0):
        p = {'ubicacion': 'freezer', 'fecha_extraccion': '2026-01-01', 'en_jardin': marca}
        params = params_base(freezer_meses=6, aviso_freezer_dias=14)
        assert logica._lac_estado(p, params, datetime(2026, 2, 1, 10, 0)) == 'disponible'


def test_una_bolsita_de_heladera_del_jardin_dice_que_esta_en_el_jardin():
    # La que se fue con León ya descongelada.
    p = {'ubicacion': 'heladera', 'tipo': 'fresca', 'en_jardin': 1,
         'fecha_extraccion': '2026-07-01', 'hora_extraccion': '08:00'}
    params = params_base(heladera_horas=48, aviso_heladera_horas=12)  # vence 3/7 08:00
    assert logica._lac_estado(p, params, datetime(2026, 7, 2, 10, 0)) == 'en_jardin'


def test_en_la_heladera_el_aviso_tambien_le_gana_a_la_marca_del_jardin():
    # Acá importa más todavía: el reloj de la heladera corre en horas.
    p = {'ubicacion': 'heladera', 'tipo': 'fresca', 'en_jardin': 1,
         'fecha_extraccion': '2026-07-01', 'hora_extraccion': '08:00'}
    params = params_base(heladera_horas=48, aviso_heladera_horas=12)
    assert logica._lac_estado(p, params, datetime(2026, 7, 2, 20, 0)) == 'vence_pronto'
    assert logica._lac_estado(p, params, datetime(2026, 7, 3, 9, 0)) == 'vencida'


def test_heladera_avisa_justo_cuando_faltan_las_horas_configuradas():
    p = {'ubicacion': 'heladera', 'tipo': 'fresca',
         'fecha_extraccion': '2026-07-01', 'hora_extraccion': '08:00'}
    params = params_base(heladera_horas=48, aviso_heladera_horas=12)  # vence 3/7 08:00
    assert logica._lac_estado(p, params, datetime(2026, 7, 2, 20, 0)) == 'vence_pronto'
    assert logica._lac_estado(p, params, datetime(2026, 7, 2, 19, 0)) == 'en_heladera'
    assert logica._lac_estado(p, params, datetime(2026, 7, 3, 9, 0)) == 'vencida'


def test_la_leche_descongelada_usa_su_propio_aviso_mas_corto():
    # Con 7 horas por delante, una leche FRESCA todavía no avisaría (su aviso es
    # de 12 h) pero una DESCONGELADA tampoco (el suyo es de 6 h). A las 6 h justas
    # sí. Esta prueba existe para que nunca se confundan los dos umbrales.
    p = {'ubicacion': 'heladera', 'tipo': 'descongelada',
         'fecha_extraccion': '2026-01-15', 'hora_extraccion': '08:00',
         'cargada': '2026-07-01T10:00:00'}                      # vence 2/7 10:00
    params = params_base(descongelada_horas=24, aviso_descongelada_horas=6,
                         aviso_heladera_horas=12)
    assert logica._lac_estado(p, params, datetime(2026, 7, 2, 3, 0)) == 'en_heladera'
    assert logica._lac_estado(p, params, datetime(2026, 7, 2, 4, 0)) == 'vence_pronto'


# ── Qué se puede freezar ─────────────────────────────────────────────────────
def test_una_leche_descongelada_nunca_se_puede_volver_a_freezar():
    p = {'ubicacion': 'heladera', 'tipo': 'descongelada',
         'fecha_extraccion': '2026-07-01', 'hora_extraccion': '08:00',
         'cargada': '2026-07-01T10:00:00'}
    assert logica._lac_freezable(p, params_base(), datetime(2026, 7, 1, 12, 0)) is False


def test_una_leche_de_heladera_fresca_y_al_dia_se_puede_freezar():
    p = {'ubicacion': 'heladera', 'tipo': 'fresca',
         'fecha_extraccion': '2026-07-01', 'hora_extraccion': '08:00'}
    assert logica._lac_freezable(p, params_base(), datetime(2026, 7, 1, 12, 0)) is True


def test_no_se_freeza_lo_vencido_ni_lo_ya_cerrado_ni_lo_que_ya_esta_en_el_freezer():
    params = params_base(heladera_horas=48)
    vencida = {'ubicacion': 'heladera', 'tipo': 'fresca',
               'fecha_extraccion': '2026-07-01', 'hora_extraccion': '08:00'}
    assert logica._lac_freezable(vencida, params, datetime(2026, 7, 5, 8, 0)) is False

    cerrada = {'ubicacion': 'heladera', 'tipo': 'fresca', 'motivo_cierre': 'usada',
               'fecha_extraccion': '2026-07-01', 'hora_extraccion': '08:00'}
    assert logica._lac_freezable(cerrada, params, datetime(2026, 7, 1, 12, 0)) is False

    del_freezer = {'ubicacion': 'freezer', 'fecha_extraccion': '2026-07-01'}
    assert logica._lac_freezable(del_freezer, params, datetime(2026, 7, 1, 12, 0)) is False


# ── Día y mes de vida del bebé ───────────────────────────────────────────────
def test_el_dia_del_parto_es_el_dia_1_y_el_mes_1():
    assert logica._lac_dia_de_vida(date(2026, 5, 14), date(2026, 5, 14)) == (1, 1)
    assert logica._lac_dia_de_vida(date(2026, 5, 14), date(2026, 5, 15)) == (2, 1)


def test_el_mes_de_vida_cambia_el_mismo_numero_de_dia():
    nac = date(2026, 5, 14)
    assert logica._lac_dia_de_vida(nac, date(2026, 6, 13)) == (31, 1)   # víspera
    assert logica._lac_dia_de_vida(nac, date(2026, 6, 14)) == (32, 2)   # cumple mes


def test_sin_fecha_de_nacimiento_o_antes_de_nacer_no_hay_dia_de_vida():
    assert logica._lac_dia_de_vida(None, date(2026, 5, 14)) == (None, None)
    assert logica._lac_dia_de_vida(date(2026, 5, 14), date(2026, 5, 13)) == (None, None)


# ── Las configuraciones de cada mamá ─────────────────────────────────────────
def test_una_mama_que_no_toco_nada_usa_los_valores_por_defecto():
    params = logica._lac_params(perfil={})
    assert params['freezer_meses'] == 6
    assert params['heladera_horas'] == 48
    assert params['bolsa_capacidad_activa'] is False


def test_un_cero_configurado_vale_como_cero_y_no_como_vacio():
    # El error clásico sería tratar el 0 como "no configurado" y volver al 3 por
    # defecto. Una mamá que apagó la espera para combinar tiene que ver un 0.
    params = logica._lac_params(perfil={'combinar_min_horas': 0})
    assert params['combinar_min_horas'] == 0


def test_los_valores_propios_de_la_mama_le_ganan_a_los_de_fabrica():
    params = logica._lac_params(perfil={'freezer_meses': 12, 'heladera_horas': 72,
                                        'bolsa_capacidad_activa': 1})
    assert params['freezer_meses'] == 12
    assert params['heladera_horas'] == 72
    assert params['bolsa_capacidad_activa'] is True
