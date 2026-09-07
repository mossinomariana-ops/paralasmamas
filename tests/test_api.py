# =============================================================================
# test_api.py — La app entera, botón por botón.
# =============================================================================
# Acá no se prueban funciones sueltas sino la app funcionando: se abre una
# sesión de mamá, se aprietan los botones (los mismos pedidos que manda el
# JavaScript) y se mira qué contesta. Es lo más parecido a usarla a mano, pero
# en segundos y sin olvidarse ningún caso.
# =============================================================================

from datetime import date, datetime, timedelta

import pytest

from conftest import crear, crear_id, payload, post


# ── Cargar leche ─────────────────────────────────────────────────────────────
def test_cargar_una_bolsita_al_freezer_y_verla_en_la_lista(cliente):
    datos = crear(cliente, ubicacion='freezer', volumen_ml=120).get_json()
    assert datos['ok']
    assert len(datos['freezer']) == 1
    assert datos['freezer'][0]['volumen_ml'] == 120
    assert datos['tablero']['freezer_ml'] == 120


def test_cargar_una_bolsita_a_la_heladera(cliente):
    datos = crear(cliente, ubicacion='heladera', volumen_ml=80).get_json()
    assert datos['ok']
    assert len(datos['heladera']) == 1
    assert datos['heladera'][0]['tipo'] == 'fresca'
    assert datos['tablero']['heladera_ml'] == 80


def test_una_mama_recien_llegada_ve_todo_en_cero(cliente):
    datos = payload(cliente)
    assert datos['freezer'] == [] and datos['heladera'] == [] and datos['historial'] == []
    assert datos['tablero']['freezer_ml'] == 0
    assert datos['badge'] == 0


def test_las_bolsitas_se_ordenan_por_lo_que_vence_primero(cliente):
    # FIFO: la leche más vieja va primera, para usarla antes de que se venza.
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=1)
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=30)
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=10)
    fechas = [p['fecha_extraccion'] for p in payload(cliente)['freezer']]
    assert fechas == sorted(fechas)


# ── Errores de carga ─────────────────────────────────────────────────────────
def test_un_volumen_imposible_se_rechaza_con_un_mensaje_y_no_con_una_pantalla_de_error(cliente):
    r = crear(cliente, volumen_ml=3000)
    assert r.status_code == 400              # y NO 500: es culpa del dato, no de la app
    datos = r.get_json()
    assert datos['ok'] is False
    assert datos['error']                     # hay un mensaje para mostrarle
    assert payload(cliente)['freezer'] == []  # y no se guardó nada


def test_una_extraccion_del_futuro_se_rechaza(cliente):
    r = crear(cliente, dias_atras=-1)
    assert r.status_code == 400
    assert payload(cliente)['freezer'] == []


# ── Usar, descartar y deshacer ───────────────────────────────────────────────
def test_usar_una_bolsita_la_manda_al_historial(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    datos = post(cliente, f'/api/lactancia/{pid}/cerrar',
                 motivo='usada', consumido_ml=80).get_json()
    assert datos['ok']
    assert datos['freezer'] == []
    assert len(datos['historial']) == 1
    assert datos['historial'][0]['estado'] == 'usada'
    assert datos['tablero']['consumida_ml'] == 80
    assert datos['tablero']['desperdicio_ml'] == 20     # los 20 ml que sobraron


def test_descartar_una_bolsita_cuenta_como_desperdicio(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    datos = post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='descartada').get_json()
    assert datos['tablero']['desperdicio_ml'] == 100
    assert datos['tablero']['descartadas_total'] == 1


def test_deshacer_devuelve_la_bolsita_a_su_lugar(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada')
    datos = post(cliente, f'/api/lactancia/{pid}/reabrir').get_json()
    assert datos['ok']
    assert len(datos['freezer']) == 1
    assert datos['historial'] == []


def test_no_se_puede_decir_que_tomo_mas_de_lo_que_habia_en_la_bolsita(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    r = post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada', consumido_ml=150)
    assert r.status_code == 400
    assert '100' in r.get_json()['error']    # el mensaje dice cuánto había


def test_no_se_puede_cerrar_dos_veces_la_misma_bolsita(cliente):
    pid = crear_id(cliente, ubicacion='freezer')
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada')
    r = post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='descartada')
    assert r.status_code == 400


@pytest.mark.parametrize('motivo', ['', 'perdida', 'trasladada'])
def test_solo_se_puede_cerrar_como_usada_o_descartada(cliente, motivo):
    # 'trasladada' existe en la base, pero es interna: la pone la app cuando se
    # freeza, no puede llegar desde un formulario.
    pid = crear_id(cliente, ubicacion='freezer')
    assert post(cliente, f'/api/lactancia/{pid}/cerrar',
                motivo=motivo).status_code == 400


def test_una_bolsita_que_no_existe_da_un_error_claro_y_no_un_choque(cliente):
    for url in ('/api/lactancia/9999/cerrar', '/api/lactancia/9999/editar',
                '/api/lactancia/9999/eliminar', '/api/lactancia/9999/reabrir'):
        r = post(cliente, url, motivo='usada', volumen_ml=100)
        assert r.status_code == 400, url
        assert r.get_json()['ok'] is False


# ── El back up del jardín ────────────────────────────────────────────────────
# Marcar una bolsita como "está en el jardín" NO la cierra ni la saca del
# freezer: solo dice dónde está guardada. Todo lo que la mamá mira para saber
# cuánta leche tiene tiene que quedar igual.
def test_marcar_una_bolsita_como_back_up_del_jardin(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    datos = post(cliente, f'/api/lactancia/{pid}/jardin', en_jardin='1').get_json()
    assert datos['ok']
    p = datos['freezer'][0]
    assert p['en_jardin'] is True
    assert p['estado'] == 'en_jardin'
    assert p['motivo_cierre'] is None           # no se cerró nada
    assert datos['historial'] == []             # no cayó al historial


def test_la_bolsita_del_jardin_sigue_contando_como_stock(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    antes = payload(cliente)['tablero']
    datos = post(cliente, f'/api/lactancia/{pid}/jardin', en_jardin='1').get_json()
    ahora = datos['tablero']
    assert ahora['freezer_ml'] == antes['freezer_ml']
    assert ahora['freezer_bolsas'] == antes['freezer_bolsas']
    assert (ahora['jardin_bolsas'], ahora['jardin_ml']) == (1, 120)


def test_sacar_la_bolsita_del_jardin_la_deja_como_estaba(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    post(cliente, f'/api/lactancia/{pid}/jardin', en_jardin='1')
    datos = post(cliente, f'/api/lactancia/{pid}/jardin', en_jardin='0').get_json()
    p = datos['freezer'][0]
    assert p['en_jardin'] is False
    assert p['estado'] == 'disponible'
    assert datos['tablero']['jardin_bolsas'] == 0


def test_una_bolsita_recien_cargada_no_esta_en_el_jardin(cliente):
    datos = crear(cliente, ubicacion='freezer', volumen_ml=100).get_json()
    assert datos['freezer'][0]['en_jardin'] is False
    assert datos['tablero']['jardin_bolsas'] == 0


def test_la_leche_de_la_heladera_tambien_puede_estar_en_el_jardin(cliente):
    # El día que León se va con una bolsita ya descongelada: está en la heladera
    # del jardín, no en la de casa.
    pid = crear_id(cliente, ubicacion='heladera', volumen_ml=80)
    datos = post(cliente, f'/api/lactancia/{pid}/jardin', en_jardin='1').get_json()
    assert datos['ok']
    p = datos['heladera'][0]
    assert p['en_jardin'] is True
    assert p['estado'] == 'en_jardin'
    assert datos['freezer'] == []                 # no se cambió de lista
    assert datos['tablero']['jardin_bolsas'] == 1


def test_la_leche_del_jardin_sigue_sumando_al_stock_de_la_heladera(cliente):
    pid = crear_id(cliente, ubicacion='heladera', volumen_ml=80)
    antes = payload(cliente)['tablero']
    ahora = post(cliente, f'/api/lactancia/{pid}/jardin',
                 en_jardin='1').get_json()['tablero']
    assert ahora['heladera_ml'] == antes['heladera_ml']
    assert ahora['heladera_bolsas'] == antes['heladera_bolsas']


def test_al_bajarla_del_freezer_la_marca_del_jardin_la_sigue(cliente):
    # El back up que el jardín descongeló allá: la bolsita nueva sigue estando
    # en el jardín, no aparece de golpe en la heladera de casa.
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    post(cliente, f'/api/lactancia/{pid}/jardin', en_jardin='1')
    datos = post(cliente, f'/api/lactancia/{pid}/bajar').get_json()
    nueva = datos['heladera'][0]
    assert nueva['tipo'] == 'descongelada'
    assert nueva['en_jardin'] is True
    assert nueva['estado'] == 'en_jardin'


def test_una_bolsita_de_casa_al_bajarla_sigue_siendo_de_casa(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    datos = post(cliente, f'/api/lactancia/{pid}/bajar').get_json()
    assert datos['heladera'][0]['en_jardin'] is False


def test_una_bolsita_ya_cerrada_no_se_puede_mandar_al_jardin(cliente):
    pid = crear_id(cliente, ubicacion='freezer')
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada')
    assert post(cliente, f'/api/lactancia/{pid}/jardin',
                en_jardin='1').status_code == 400


def test_la_marca_del_jardin_sobrevive_al_cierre_y_a_la_reapertura(cliente):
    # Si el jardín se la terminó dando a León, el historial tiene que seguir
    # diciendo que esa bolsita estaba allá.
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    post(cliente, f'/api/lactancia/{pid}/jardin', en_jardin='1')
    datos = post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada').get_json()
    assert datos['historial'][0]['en_jardin'] is True
    datos = post(cliente, f'/api/lactancia/{pid}/reabrir').get_json()
    assert datos['freezer'][0]['estado'] == 'en_jardin'


def test_los_dias_de_stock_cuentan_el_freezer_la_heladera_y_el_jardin(cliente):
    # "Alcanza para" mide TODA la leche que León tiene para tomar, esté donde
    # esté. Con 700 ml y un consumo de 100 ml/día, son 7 días.
    usada = crear_id(cliente, ubicacion='freezer', volumen_ml=700)
    post(cliente, f'/api/lactancia/{usada}/cerrar', motivo='usada')   # 700 en 7 días
    crear_id(cliente, ubicacion='freezer', volumen_ml=300)
    jardin = crear_id(cliente, ubicacion='freezer', volumen_ml=200)
    post(cliente, f'/api/lactancia/{jardin}/jardin', en_jardin='1')
    en_el_jardin = crear_id(cliente, ubicacion='heladera', volumen_ml=200)
    post(cliente, f'/api/lactancia/{en_el_jardin}/jardin', en_jardin='1')
    assert payload(cliente)['tablero']['dias_stock'] == 7             # 700 / 100


# ── Editar y eliminar ────────────────────────────────────────────────────────
def test_editar_cambia_el_volumen_y_la_fecha(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    ayer = (date.today() - timedelta(days=1)).isoformat()
    datos = post(cliente, f'/api/lactancia/{pid}/editar', volumen_ml=90,
                 fecha_extraccion=ayer, hora_extraccion='06:30',
                 notas='corregida').get_json()
    p = datos['freezer'][0]
    assert (p['volumen_ml'], p['fecha_extraccion'], p['notas']) == (90, ayer, 'corregida')


def test_eliminar_borra_la_bolsita_para_siempre(cliente):
    pid = crear_id(cliente, ubicacion='freezer')
    datos = post(cliente, f'/api/lactancia/{pid}/eliminar').get_json()
    assert datos['freezer'] == [] and datos['historial'] == []


# ── Freezar: juntar varias de la heladera en una bolsa ───────────────────────
def test_freezar_junta_varias_bolsitas_en_una_sola(cliente):
    a = crear_id(cliente, ubicacion='heladera', volumen_ml=60, dias_atras=1)
    b = crear_id(cliente, ubicacion='heladera', volumen_ml=40, dias_atras=1)
    datos = post(cliente, '/api/lactancia/freezar', ids=f'{a},{b}').get_json()
    assert datos['ok']
    assert len(datos['freezer']) == 1
    assert datos['freezer'][0]['volumen_ml'] == 100      # 60 + 40
    assert datos['heladera'] == []
    assert [p['estado'] for p in datos['historial']] == ['trasladada', 'trasladada']


def test_deshacer_un_freezado_devuelve_todas_las_bolsitas_a_la_heladera(cliente):
    a = crear_id(cliente, ubicacion='heladera', volumen_ml=60, dias_atras=1)
    b = crear_id(cliente, ubicacion='heladera', volumen_ml=40, dias_atras=1)
    post(cliente, '/api/lactancia/freezar', ids=f'{a},{b}')
    datos = post(cliente, f'/api/lactancia/{a}/reabrir').get_json()
    assert datos['ok']
    assert datos['freezer'] == []                        # la bolsa combinada se borró
    assert len(datos['heladera']) == 2                   # y volvieron las dos
    assert datos['historial'] == []


def test_no_se_freeza_leche_vencida_sin_confirmar(cliente):
    viejo = crear_id(cliente, ubicacion='heladera', volumen_ml=60, dias_atras=5)
    r = post(cliente, '/api/lactancia/freezar', ids=str(viejo))
    assert r.status_code == 400
    # Pero si la mamá confirma que la freezó a tiempo, se le permite.
    datos = post(cliente, '/api/lactancia/freezar', ids=str(viejo),
                 confirmar_vencidas='1').get_json()
    assert datos['ok']


def test_no_se_puede_armar_una_bolsa_de_mas_de_2000_ml(cliente):
    a = crear_id(cliente, ubicacion='heladera', volumen_ml=1500, dias_atras=1)
    b = crear_id(cliente, ubicacion='heladera', volumen_ml=1500, dias_atras=1)
    r = post(cliente, '/api/lactancia/freezar', ids=f'{a},{b}')
    assert r.status_code == 400
    assert len(payload(cliente)['heladera']) == 2        # no se tocó nada


def test_no_se_freeza_algo_que_ya_esta_en_el_freezer(cliente):
    pid = crear_id(cliente, ubicacion='freezer')
    assert post(cliente, '/api/lactancia/freezar', ids=str(pid)).status_code == 400


def test_freezar_sin_tildar_nada_avisa(cliente):
    assert post(cliente, '/api/lactancia/freezar', ids='').status_code == 400


# ── Bajar del freezer a descongelar ──────────────────────────────────────────
def test_bajar_una_bolsa_la_deja_descongelando_en_la_heladera(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    datos = post(cliente, f'/api/lactancia/{pid}/bajar').get_json()
    assert datos['ok']
    assert datos['freezer'] == []
    assert len(datos['heladera']) == 1
    nueva = datos['heladera'][0]
    assert nueva['tipo'] == 'descongelada'
    assert nueva['volumen_ml'] == 100
    assert nueva['freezable'] is False        # lo descongelado no se recongela


def test_no_se_puede_bajar_dos_veces_la_misma_bolsa(cliente):
    pid = crear_id(cliente, ubicacion='freezer')
    post(cliente, f'/api/lactancia/{pid}/bajar')
    assert post(cliente, f'/api/lactancia/{pid}/bajar').status_code == 400


# ── Corregir a qué hora la bajaste de verdad ─────────────────────────────────
# Se baja la bolsita en la cocina y recién se carga en la app un rato después.
# Como la leche descongelada se cuenta desde que salió del freezer y no desde el
# toque en la pantalla, esa hora se puede corregir en el editor.
def editar(cliente, pid, p, **cambios):
    """Reenvía el editor con lo que la bolsita ya tiene, cambiando solo lo que se
    pida — igual que el modal, que llega precargado."""
    campos = {'volumen_ml': p['volumen_ml'], 'notas': p['notas'] or '',
              'fecha_extraccion': p['fecha_extraccion'],
              'hora_extraccion': p['hora_extraccion'] or '00:00'}
    campos.update(cambios)
    return post(cliente, f'/api/lactancia/{pid}/editar', **campos)


def bajar(cliente, dias_atras=2):
    """Una bolsita ya bajada del freezer, lista para corregirle la hora."""
    pid = crear_id(cliente, ubicacion='freezer', dias_atras=dias_atras)
    datos = post(cliente, f'/api/lactancia/{pid}/bajar').get_json()
    assert datos['ok'], datos
    return pid, datos['heladera'][0], datos['params']['descongelada_horas']


def test_corregir_la_hora_en_que_la_bajaste_le_corre_el_vencimiento(cliente):
    _, p, horas = bajar(cliente)
    bajada = datetime.fromisoformat(p['cargada']) - timedelta(hours=3)
    datos = editar(cliente, p['id'], p,
                   fecha_bajada=bajada.date().isoformat(),
                   hora_bajada=bajada.strftime('%H:%M')).get_json()
    assert datos['ok'], datos
    corregida = datos['heladera'][0]
    assert corregida['cargada'] == bajada.strftime('%Y-%m-%dT%H:%M:00')
    # El vencimiento se cuenta desde la hora corregida, no desde el toque.
    esperado = bajada.replace(second=0, microsecond=0) + timedelta(hours=horas)
    assert datetime.fromisoformat(corregida['vencimiento']) == esperado
    assert corregida['horas_restantes'] < p['horas_restantes']


def test_si_la_bajaste_hace_mucho_la_app_te_la_muestra_vencida(cliente):
    # El caso que importa de verdad: la app tiene que avisar que esa leche ya no
    # va, en vez de regalarle horas de vida útil que no tuvo.
    _, p, horas = bajar(cliente, dias_atras=20)
    bajada = datetime.now() - timedelta(hours=horas + 1)
    datos = editar(cliente, p['id'], p,
                   fecha_bajada=bajada.date().isoformat(),
                   hora_bajada=bajada.strftime('%H:%M')).get_json()
    assert datos['heladera'][0]['estado'] == 'vencida'


def test_no_se_puede_decir_que_la_bajaste_en_el_futuro(cliente):
    _, p, _ = bajar(cliente)
    manana = date.today() + timedelta(days=1)
    r = editar(cliente, p['id'], p,
               fecha_bajada=manana.isoformat(), hora_bajada='12:00')
    assert r.status_code == 400
    assert r.get_json()['ok'] is False


def test_no_pudiste_bajarla_antes_de_haberte_extraido_la_leche(cliente):
    _, p, _ = bajar(cliente, dias_atras=2)
    antes_de_extraer = date.today() - timedelta(days=3)
    r = editar(cliente, p['id'], p,
               fecha_bajada=antes_de_extraer.isoformat(), hora_bajada='10:00')
    assert r.status_code == 400
    assert r.get_json()['ok'] is False


def test_a_una_bolsita_que_no_se_descongelo_no_le_cambia_nada(cliente):
    # En una fresca `cargada` es solo el sello de cuándo se cargó el dato: su
    # vencimiento sale de la extracción, así que el campo ni se muestra.
    pid = crear_id(cliente, ubicacion='heladera', dias_atras=1)
    p = payload(cliente)['heladera'][0]
    ayer = date.today() - timedelta(days=1)
    datos = editar(cliente, pid, p,
                   fecha_bajada=ayer.isoformat(), hora_bajada='05:00').get_json()
    assert datos['ok'], datos
    assert datos['heladera'][0]['cargada'] == p['cargada']


def test_editar_sin_tocar_la_bajada_deja_la_hora_como_estaba(cliente):
    # El pedido que manda la app cuando solo se corrige un volumen.
    _, p, _ = bajar(cliente)
    datos = editar(cliente, p['id'], p, volumen_ml=77).get_json()
    assert datos['heladera'][0]['volumen_ml'] == 77
    assert datos['heladera'][0]['cargada'] == p['cargada']


def test_al_corregir_el_dia_el_historial_no_dice_que_la_bajaste_hoy(cliente):
    pid, p, _ = bajar(cliente, dias_atras=3)
    anoche = date.today() - timedelta(days=1)
    datos = editar(cliente, p['id'], p,
                   fecha_bajada=anoche.isoformat(), hora_bajada='22:00').get_json()
    vieja = [h for h in datos['historial'] if h['id'] == pid][0]
    assert vieja['fecha_cierre'] == anoche.isoformat()


# ── Configuraciones ──────────────────────────────────────────────────────────
def test_cambiar_los_tiempos_cambia_los_vencimientos(cliente):
    crear(cliente, ubicacion='freezer', volumen_ml=100)
    antes = payload(cliente)['freezer'][0]['dias_restantes']
    assert post(cliente, '/api/lactancia/config', freezer_meses=12).get_json()['ok']
    despues = payload(cliente)['freezer'][0]['dias_restantes']
    assert despues > antes                    # 12 meses dura más que 6


@pytest.mark.parametrize('campo,valor', [
    ('freezer_meses', 99),          # el máximo es 24
    ('freezer_meses', 0),           # el mínimo es 1
    ('heladera_horas', 1000),       # el máximo es 168
    ('bolsa_capacidad_ml', 5),      # el mínimo es 10
    ('freezer_meses', 'seis'),      # ni siquiera es un número
])
def test_una_configuracion_fuera_de_rango_se_rechaza(cliente, campo, valor):
    r = post(cliente, '/api/lactancia/config', **{campo: valor})
    assert r.status_code == 400
    assert r.get_json()['error']


def test_no_se_puede_avisar_despues_de_que_la_leche_ya_venci(cliente):
    # El aviso de la heladera (60 h) no puede ser mayor que el vencimiento (48 h):
    # sería un aviso que llega tarde siempre.
    assert post(cliente, '/api/lactancia/config',
                aviso_heladera_horas=60).status_code == 400
    assert post(cliente, '/api/lactancia/config',
                aviso_descongelada_horas=48, descongelada_horas=24).status_code == 400


def test_guardar_sin_mandar_ninguna_configuracion_avisa(cliente):
    assert post(cliente, '/api/lactancia/config').status_code == 400


# ── Recordatorio, bebé e idioma ──────────────────────────────────────────────
def test_guardar_el_recordatorio_de_la_noche(cliente):
    datos = post(cliente, '/api/lactancia/recordatorio',
                 activo='1', hora='21:30').get_json()
    assert datos['recordatorio']['activo'] is True
    assert datos['recordatorio']['hora'] == '21:30'


@pytest.mark.parametrize('hora', ['', '9pm', '25:00', '21'])
def test_una_hora_de_recordatorio_invalida_se_rechaza(cliente, hora):
    assert post(cliente, '/api/lactancia/recordatorio',
                activo='1', hora=hora).status_code == 400


def test_guardar_dias_de_jardin_del_recordatorio(cliente):
    datos = post(cliente, '/api/lactancia/recordatorio',
                 activo='1', hora='21:30', dias='0,2,4').get_json()
    assert datos['recordatorio']['dias'] == [0, 2, 4]


def test_sin_mandar_dias_se_mantienen_los_que_ya_estaban(cliente):
    post(cliente, '/api/lactancia/recordatorio', activo='1', hora='21:30', dias='1,3')
    datos = post(cliente, '/api/lactancia/recordatorio',
                 activo='1', hora='22:00').get_json()
    assert datos['recordatorio']['dias'] == [1, 3]


@pytest.mark.parametrize('dias', ['7', '-1', 'lunes', '1,x,3'])
def test_dias_de_recordatorio_invalidos_se_rechazan(cliente, dias):
    assert post(cliente, '/api/lactancia/recordatorio',
                activo='1', hora='21:00', dias=dias).status_code == 400


def test_guardar_los_datos_del_bebe_calcula_su_edad(cliente):
    nac = (date.today() - timedelta(days=40)).isoformat()
    datos = post(cliente, '/api/lactancia/bebe',
                 nombre='León', fecha_nacimiento=nac).get_json()
    assert datos['bebe']['nombre'] == 'León'
    assert datos['bebe']['mes_de_vida'] == 2          # ya cumplió el mes
    assert datos['bebe']['edad_texto']                # "1 mes y N días"


def test_un_bebe_no_puede_haber_nacido_manana(cliente):
    manana = (date.today() + timedelta(days=1)).isoformat()
    assert post(cliente, '/api/lactancia/bebe',
                nombre='León', fecha_nacimiento=manana).status_code == 400


def test_cambiar_el_idioma_pide_recargar_la_pantalla(cliente):
    datos = post(cliente, '/api/lactancia/idioma', idioma='en').get_json()
    assert datos['ok'] and datos['recargar'] is True


def test_un_idioma_que_la_app_no_habla_se_rechaza(cliente):
    assert post(cliente, '/api/lactancia/idioma', idioma='fr').status_code == 400


# ── La descarga para Excel ───────────────────────────────────────────────────
def test_la_descarga_sale_lista_para_abrir_en_excel(cliente):
    nac = (date.today() - timedelta(days=3)).isoformat()
    post(cliente, '/api/lactancia/bebe', nombre='León', fecha_nacimiento=nac)
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=2)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada', consumido_ml=90)

    r = cliente.get('/descargar/dia-a-dia.csv')
    assert r.status_code == 200
    assert 'attachment' in r.headers['Content-Disposition']

    texto = r.get_data(as_text=True)
    assert texto.startswith('﻿')          # la marca que Excel necesita
    assert ';' in texto.split('\r\n')[0]       # en español el separador es ;
    assert 'Totales' in texto
    # Un renglón por día desde el nacimiento hasta hoy: 4 días + encabezado + totales
    assert len([l for l in texto.strip().split('\r\n') if l]) == 6
    assert '90' in texto                       # los ml que tomó


def test_en_ingles_la_descarga_usa_la_coma_como_separador(cliente):
    post(cliente, '/api/lactancia/idioma', idioma='en')
    texto = cliente.get('/descargar/dia-a-dia.csv').get_data(as_text=True)
    encabezado = texto.split('\r\n')[0]
    assert ',' in encabezado and ';' not in encabezado
    assert 'Date' in encabezado


# ── La app instalable (PWA) ──────────────────────────────────────────────────
def test_el_manifiesto_de_la_app_instalable_esta_completo(cliente):
    r = cliente.get('/manifest.webmanifest')
    assert r.status_code == 200
    m = r.get_json()
    assert m['start_url'] == '/' and m['display'] == 'standalone'
    assert len(m['icons']) == 3


def test_el_manifiesto_tiene_lo_que_pide_google_play(cliente):
    m = cliente.get('/manifest.webmanifest').get_json()
    # `id` es la identidad de la app. Si cambia, Android la toma por otra
    # distinta y la que las mamás ya tienen instalada queda huérfana. "/" es el
    # mismo valor que el navegador calculaba solo antes de que existiera este
    # campo, así que ponerlo no rompe ninguna instalación.
    assert m['id'] == '/'
    assert m['dir'] == 'ltr'
    assert 'standalone' in m['display_override']
    assert m['categories']
    assert {c['form_factor'] for c in m['screenshots']} >= {'narrow', 'wide'}


def test_las_capturas_de_un_mismo_formato_tienen_la_misma_forma(cliente):
    # Chrome descarta la pantalla linda de instalación ENTERA si dos capturas
    # del mismo formato tienen proporciones distintas.
    m = cliente.get('/manifest.webmanifest').get_json()
    for formato in ('narrow', 'wide'):
        medidas = {c['sizes'] for c in m['screenshots']
                   if c['form_factor'] == formato}
        assert len(medidas) == 1, (formato, medidas)


def test_no_hay_ningun_icono_ni_captura_rota(cliente):
    # Un archivo prometido en el manifiesto pero ausente hace fallar el
    # empaquetado para la tienda, y es imposible de ver a ojo.
    m = cliente.get('/manifest.webmanifest').get_json()
    for item in m['icons'] + m['screenshots']:
        assert cliente.get(item['src']).status_code == 200, item['src']


def test_las_capturas_miden_lo_que_dice_el_manifiesto(cliente):
    # Si `sizes` no coincide al píxel con el archivo, Chrome ignora la captura
    # sin avisar. Se comprueba leyendo el encabezado del PNG: los 8 bytes de la
    # firma, después el bloque IHDR con ancho y alto en 4 bytes cada uno.
    import struct
    m = cliente.get('/manifest.webmanifest').get_json()
    for captura in m['screenshots']:
        crudo = cliente.get(captura['src']).get_data()
        ancho, alto = struct.unpack('>II', crudo[16:24])
        assert f'{ancho}x{alto}' == captura['sizes'], captura['src']


def test_el_manifiesto_se_sirve_con_su_propio_tipo(cliente):
    r = cliente.get('/manifest.webmanifest')
    assert r.mimetype == 'application/manifest+json'


def test_el_service_worker_se_sirve_con_los_permisos_correctos(cliente):
    r = cliente.get('/sw.js')
    assert r.status_code == 200
    # Sin esta cabecera el service worker solo controlaría /static/, y la app no
    # funcionaría sin internet.
    assert r.headers['Service-Worker-Allowed'] == '/'
    assert r.headers['Cache-Control'] == 'no-cache'


# ── La pantalla principal ────────────────────────────────────────────────────
def test_la_pantalla_principal_abre_y_muestra_la_leche_cargada(cliente):
    crear(cliente, ubicacion='freezer', volumen_ml=123)
    r = cliente.get('/')
    assert r.status_code == 200
    assert '123' in r.get_data(as_text=True)
