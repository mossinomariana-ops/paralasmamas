# =============================================================================
# test_contrato_payload.py — El acuerdo entre el servidor y la pantalla.
# =============================================================================
# En esta app los vencimientos se calculan en UN SOLO lugar: el servidor
# (logica.py). El JavaScript no calcula nada, solo dibuja lo que recibe. Está
# muy bien que sea así, pero deja una costura: si alguna vez alguien le cambia
# el nombre a un campo en el servidor, el navegador no se rompe con un error
# visible — simplemente muestra un espacio en blanco, o un "—", y nadie se
# entera hasta que una mamá no ve cuándo vence su leche.
#
# Estas pruebas cierran esa costura: comprueban que el servidor mande SIEMPRE
# todos los datos que la pantalla busca, y con el tipo de dato correcto.
#
# Las listas de abajo están copiadas de static/lactancia.js. Si se cambia una
# allá y no acá (o al revés), estas pruebas avisan.
# =============================================================================

from datetime import date, timedelta

import pytest

from conftest import crear, crear_id, payload, post

# Campos que el JavaScript lee de CADA bolsita (itemFreezer, itemHeladera,
# itemHistorial y extraidaTxt en lactancia.js).
CAMPOS_COMUNES = ['id', 'volumen_ml', 'estado', 'vencimiento',
                  'fecha_extraccion', 'hora_extraccion', 'notas',
                  'ubicacion', 'tipo', 'motivo_cierre', 'fecha_cierre']

# Los estados que el JavaScript sabe dibujar (ESTADO_LABEL, lactancia.js:165).
# Un estado que no esté en esta lista saldría en pantalla como texto crudo.
ESTADOS_CONOCIDOS = {'disponible', 'vence_pronto', 'vencida', 'en_heladera',
                     'usada', 'descartada', 'trasladada'}

# Configuraciones que el JavaScript pinta en la pantalla de ajustes
# (CFG_NUM y CFG_BOOL, lactancia.js:1062).
CFG_NUM = ['freezer_meses', 'heladera_horas', 'descongelada_horas',
           'aviso_freezer_dias', 'aviso_heladera_horas',
           'aviso_descongelada_horas', 'combinar_min_horas',
           'freezar_hasta_horas', 'bolsa_capacidad_ml']
CFG_BOOL = ['bolsa_capacidad_activa', 'pedir_confirmacion']

# Números del tablero de arriba (renderTablero, lactancia.js:371).
TABLERO = ['freezer_bolsas', 'freezer_ml', 'freezer_vence_pronto',
           'freezer_vencidas', 'freezer_proximo_venc', 'usadas_total',
           'descartadas_total', 'heladera_bolsas', 'heladera_ml',
           'producido_ml', 'descongelada_ml', 'consumida_ml',
           'desperdicio_ml', 'dias_stock', 'bolsa_sugerida_ml']


def test_el_payload_trae_todas_las_secciones_que_la_pantalla_espera(cliente):
    datos = payload(cliente)
    for seccion in ('freezer', 'heladera', 'historial', 'tablero', 'params',
                    'badge', 'recordatorio', 'bebe'):
        assert seccion in datos, seccion


def test_una_bolsita_de_freezer_trae_los_dias_que_le_quedan(cliente):
    crear(cliente, ubicacion='freezer', volumen_ml=100)
    p = payload(cliente)['freezer'][0]

    for campo in CAMPOS_COMUNES:
        assert campo in p, campo
    # El freezer se cuenta en DÍAS. `horas_restantes` tiene que venir vacío: si
    # viniera con un número, la pantalla mostraría dos cuentas distintas.
    assert isinstance(p['dias_restantes'], int)
    assert p['horas_restantes'] is None
    assert p['vencimiento']                     # la fecha exacta, para el "(12 jul)"
    assert p['estado'] in ESTADOS_CONOCIDOS


def test_una_bolsita_de_heladera_trae_las_horas_que_le_quedan_y_si_se_puede_freezar(cliente):
    crear(cliente, ubicacion='heladera', volumen_ml=100)
    p = payload(cliente)['heladera'][0]

    for campo in CAMPOS_COMUNES:
        assert campo in p, campo
    # La heladera se cuenta en HORAS, y al revés que el freezer.
    assert isinstance(p['horas_restantes'], int)
    assert p['dias_restantes'] is None
    # Estos tres son solo de la heladera: el tilde para freezar, el "hace N
    # horas que está" y si viene tildado por defecto.
    assert isinstance(p['freezable'], bool)
    assert isinstance(p['horas_en_heladera'], int)
    assert isinstance(p['freezar_reciente'], bool)
    assert p['estado'] in ESTADOS_CONOCIDOS


def test_el_historial_trae_el_motivo_y_la_fecha_del_cierre(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada', consumido_ml=90)
    p = payload(cliente)['historial'][0]

    for campo in CAMPOS_COMUNES:
        assert campo in p, campo
    assert p['motivo_cierre'] == 'usada'
    assert p['fecha_cierre'] == date.today().isoformat()
    assert p['estado'] in ESTADOS_CONOCIDOS


def test_ningun_estado_sale_con_un_nombre_que_la_pantalla_no_sepa_dibujar(cliente):
    # Se arma una app con leche de todo tipo: al día, por vencer, vencida,
    # usada, descartada, freezada y descongelada.
    crear(cliente, ubicacion='freezer', volumen_ml=100)                  # al día
    crear(cliente, ubicacion='heladera', volumen_ml=50, dias_atras=5)    # vencida
    usada = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{usada}/cerrar', motivo='usada')
    tirada = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{tirada}/cerrar', motivo='descartada')
    fresca = crear_id(cliente, ubicacion='heladera', volumen_ml=60, dias_atras=1)
    post(cliente, '/api/lactancia/freezar', ids=str(fresca))             # trasladada
    baja = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{baja}/bajar')                        # descongelada

    datos = payload(cliente)
    todas = datos['freezer'] + datos['heladera'] + datos['historial']
    assert len(todas) >= 7
    for p in todas:
        assert p['estado'] in ESTADOS_CONOCIDOS, p['estado']
        assert p['tipo'] in ('fresca', 'congelada', 'descongelada'), p['tipo']


def test_las_configuraciones_llegan_completas_a_la_pantalla_de_ajustes(cliente):
    params = payload(cliente)['params']
    for clave in CFG_NUM:
        assert clave in params, clave
        assert isinstance(params[clave], int), clave
    for clave in CFG_BOOL:
        assert clave in params, clave
        assert isinstance(params[clave], bool), clave


def test_el_tablero_llega_completo(cliente):
    crear(cliente, ubicacion='freezer', volumen_ml=100)
    tablero = payload(cliente)['tablero']
    for clave in TABLERO:
        assert clave in tablero, clave


def test_el_recordatorio_y_el_bebe_llegan_siempre_aunque_no_esten_configurados(cliente):
    datos = payload(cliente)
    assert set(datos['recordatorio']) == {'activo', 'hora', 'pendiente'}
    assert set(datos['bebe']) == {'nombre', 'fecha_nacimiento', 'edad_texto',
                                  'mes_de_vida'}
    # Sin nombre cargado la pantalla no puede quedar diciendo "None".
    assert datos['bebe']['nombre'] == 'el bebé'


def test_la_lista_llega_ordenada_por_lo_que_vence_primero(cliente):
    # El orden lo decide el servidor: el JavaScript dibuja la lista tal cual la
    # recibe, no la reordena.
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=0)
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=60)
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=30)
    vencimientos = [p['vencimiento'] for p in payload(cliente)['freezer']]
    assert vencimientos == sorted(vencimientos)


def test_el_numerito_de_avisos_cuenta_lo_vencido_y_lo_que_vence_pronto(cliente):
    assert payload(cliente)['badge'] == 0
    crear(cliente, ubicacion='heladera', volumen_ml=50, dias_atras=5)   # vencida
    assert payload(cliente)['badge'] == 1
    crear(cliente, ubicacion='freezer', volumen_ml=100)                 # al día
    assert payload(cliente)['badge'] == 1


def test_toda_accion_devuelve_el_estado_completo_y_no_solo_un_ok(cliente):
    # El JavaScript reemplaza TODA su información con lo que contesta cada
    # acción. Si una ruta contestara solo {ok:true}, la pantalla se vaciaría.
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    acciones = [
        ('/api/lactancia/crear', {'ubicacion': 'freezer', 'volumen_ml': 50,
                                  'fecha_extraccion': date.today().isoformat(),
                                  'hora_extraccion': '00:00'}),
        (f'/api/lactancia/{pid}/editar', {'volumen_ml': 90,
                                          'fecha_extraccion': date.today().isoformat(),
                                          'hora_extraccion': '00:00'}),
        ('/api/lactancia/config', {'freezer_meses': 8}),
        ('/api/lactancia/bebe', {'nombre': 'León', 'fecha_nacimiento': ''}),
        ('/api/lactancia/recordatorio', {'activo': '1', 'hora': '21:00'}),
        (f'/api/lactancia/{pid}/cerrar', {'motivo': 'usada'}),
        (f'/api/lactancia/{pid}/reabrir', {}),
    ]
    for url, campos in acciones:
        datos = post(cliente, url, **campos).get_json()
        assert datos['ok'], url
        for seccion in ('freezer', 'heladera', 'historial', 'tablero',
                        'params', 'badge', 'recordatorio', 'bebe'):
            assert seccion in datos, f'{url} no devolvió {seccion}'
